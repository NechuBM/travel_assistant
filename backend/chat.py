import os
import json
from backend.utils import get_openai_client
from backend.tools import AVAILABLE_TOOLS, TOOL_FUNCTIONS

def chat_with_ai_stream(message: str, conversation_history: list = None):
    """
    Main function to chat with OpenAI API with streaming and tool support.
    
    Args:
        message: User's message
        conversation_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
    
    Yields:
        Chunks of the AI's response as strings
    """
    # Load system prompt from markdown file
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'chat_assistant.md')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    
    # Prepare messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Call OpenAI API with tools
        stream = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.7,
            tools=AVAILABLE_TOOLS,
            stream=True
        )
        
        # Collect response and check for tool calls
        full_response = ""
        tool_calls = []
        
        for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle tool calls
            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    if tc_delta.index is not None:
                        # New tool call or continuation
                        while len(tool_calls) <= tc_delta.index:
                            tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                        
                        if tc_delta.id:
                            tool_calls[tc_delta.index]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls[tc_delta.index]["function"]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls[tc_delta.index]["function"]["arguments"] += tc_delta.function.arguments
            
            # Handle content
            if delta.content:
                full_response += delta.content
                yield delta.content
        
        # If tool calls were made, execute them and get final response
        if tool_calls:
            # Add assistant message with tool calls
            messages.append({
                "role": "assistant",
                "content": full_response or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    } for tc in tool_calls
                ]
            })
            
            # Execute each tool call with visible indicator
            direct_output_tools = ["generate_packing_list"]  # Tools that output directly
            needs_final_response = False
            
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                # Execute the tool
                if function_name in TOOL_FUNCTIONS:
                    # Show prominent tool usage indicator
                    yield "\n\n---\n\n"
                    yield f"**🔧 Generating packing list...**\n\n"
                    yield "---\n\n"
                    
                    result = TOOL_FUNCTIONS[function_name](**function_args)
                    
                    # For direct output tools, stream result immediately
                    if function_name in direct_output_tools:
                        # Check if result is a generator (streaming)
                        if hasattr(result, '__iter__') and not isinstance(result, str):
                            for chunk in result:
                                yield chunk
                        else:
                            yield result
                    else:
                        # For non-streaming tools, collect result
                        if hasattr(result, '__iter__') and not isinstance(result, str):
                            full_result = "".join(result)
                        else:
                            full_result = str(result)
                        
                        # Add tool response to messages for final LLM processing
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": full_result
                        })
                        needs_final_response = True
            
            # Only make final API call if needed
            if needs_final_response:
                final_stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
                
                for chunk in final_stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
    
    except Exception as e:
        yield f"Error: {str(e)}"

