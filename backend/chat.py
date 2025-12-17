import os
import json
import hashlib
from backend.utils import get_openai_client, get_runtime_context
from backend.tools import AVAILABLE_TOOLS, TOOL_FUNCTIONS

# Tool-specific loading messages
TOOL_MESSAGES = {
    "generate_packing_list": "🧳 Generating packing list...",
    "get_weather_forecast": "🌤️ Fetching weather forecast...",
    "generate_trip_plan": "🗺️ Creating your itinerary..."
}

# Tools that should always show output to user
VISIBLE_TOOLS = ["generate_packing_list", "get_weather_forecast", "generate_trip_plan"]


def _get_tool_signature(function_name: str, function_args: dict) -> str:
    """
    Create a unique signature for a tool call based on name and arguments.
    Used for deduplication to prevent calling the same tool with same args.
    """
    # Sort args to ensure consistent hashing
    args_str = json.dumps(function_args, sort_keys=True)
    signature = f"{function_name}:{args_str}"
    # Return hash for compact comparison
    return hashlib.md5(signature.encode()).hexdigest()


def _prepare_messages(system_prompt: str, conversation_history: list, user_message: str) -> list:
    """
    Prepare messages array with system prompt, runtime context, history, and user message.
    Runtime context is computed fresh and NOT persisted in conversation history.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": get_runtime_context()}
    ]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    return messages


def _collect_streaming_response(stream):
    """
    Collect response content and tool calls from a streaming API response.
    Does NOT stream to user - only collects.
    
    Returns:
        tuple: (full_response_text, tool_calls_list)
    """
    full_response = ""
    tool_calls = []
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Handle tool calls
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                if tc_delta.index is not None:
                    # Ensure tool_calls list is long enough
                    while len(tool_calls) <= tc_delta.index:
                        tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                    
                    if tc_delta.id:
                        tool_calls[tc_delta.index]["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            tool_calls[tc_delta.index]["function"]["name"] = tc_delta.function.name
                        if tc_delta.function.arguments:
                            tool_calls[tc_delta.index]["function"]["arguments"] += tc_delta.function.arguments
        
        # Collect content
        if delta.content:
            full_response += delta.content
    
    return full_response, tool_calls


def _execute_tool_and_collect(function_name: str, function_args: dict):
    """
    Execute a tool function and collect its full result.
    
    Returns:
        str: The collected result from the tool
    """
    result = TOOL_FUNCTIONS[function_name](**function_args)
    
    if hasattr(result, '__iter__') and not isinstance(result, str):
        return "".join(result)
    else:
        return str(result)


def _stream_tool_indicator(function_name: str):
    """
    Yield the visual indicator for a tool being called.
    """
    tool_msg = TOOL_MESSAGES.get(function_name, f"🔧 Using tool: {function_name}...")
    yield "\n\n---\n\n"
    yield f"**{tool_msg}**\n\n"
    yield "---\n\n"


def _execute_and_stream_tool(function_name: str, function_args: dict, is_direct_output: bool, show_output: bool = True):
    """
    Execute a tool, optionally stream output to user, and collect result.
    
    Args:
        function_name: Name of the tool to execute
        function_args: Arguments for the tool
        is_direct_output: Whether this is a direct output tool
        show_output: Whether to stream output to user
    
    Returns:
        str: Collected result from tool
    
    Yields:
        str: Chunks of output if show_output is True
    """
    result = TOOL_FUNCTIONS[function_name](**function_args)
    collected_result = ""
    
    if hasattr(result, '__iter__') and not isinstance(result, str):
        for chunk in result:
            collected_result += chunk
            if show_output:
                yield chunk
    else:
        collected_result = str(result)
        if show_output:
            yield collected_result
    
    return collected_result


def _add_assistant_message_with_tool_calls(messages: list, content: str, tool_calls: list):
    """Add assistant message with tool calls to conversation."""
    messages.append({
        "role": "assistant",
        "content": content or None,
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


def _execute_tool_calls(tool_calls: list, messages: list):
    """Execute tool calls, stream output to user, and append tool messages to conversation."""
    # Enforce single tool execution - only process first tool
    if len(tool_calls) > 1:
        tool_calls_to_execute = tool_calls[:1]
    else:
        tool_calls_to_execute = tool_calls
    
    for tool_call in tool_calls_to_execute:
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        
        if function_name not in TOOL_FUNCTIONS:
            continue
        
        for chunk in _stream_tool_indicator(function_name):
            yield chunk
        
        should_show_output = function_name in VISIBLE_TOOLS
        
        collected_result = ""
        for chunk in _execute_and_stream_tool(function_name, function_args, False, should_show_output):
            if should_show_output:
                yield chunk
            collected_result += chunk
        
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": collected_result[:1000]
        })


def chat_with_ai_stream(message: str, conversation_history: list = None):
    """
    Main chat function with streaming support for OpenAI API with tool calling.
    
    Simple flow:
        1. Call LLM with messages
        2. If tool calls → execute tools → loop back to step 1
        3. If no tool calls → done
    
    Note: Text responses after visible tools are suppressed to avoid echoing.
    
    Args:
        message: User's message
        conversation_history: List of previous messages
    
    Yields:
        Chunks of the AI's response as strings
    """
    # Load system prompt
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'chat_assistant.md')
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    
    # Prepare messages with runtime context injection
    messages = _prepare_messages(system_prompt, conversation_history, message)
    
    try:
        client = get_openai_client()
        last_tool_was_visible = False
        tools_called_history = []  # Track tool calls for deduplication: [(name, args_hash), ...]
        tools_called_names = set()  # Track which tools have been called by name
        
        for round_count in range(1, 6):  # Max 5 rounds
            # Filter out tools that have already been called
            available_tools_filtered = [
                tool for tool in AVAILABLE_TOOLS 
                if tool['function']['name'] not in tools_called_names
            ]
            
            # Call LLM
            llm_params = {
                "model": "gpt-4o",
                "messages": messages,
                "temperature": 0.7,
                "stream": True
            }
            
            # Only include tools if there are still uncalled tools available
            if available_tools_filtered:
                llm_params["tools"] = available_tools_filtered
            
            stream = client.chat.completions.create(**llm_params)
            
            # Collect response and tool calls
            full_response = ""
            tool_calls = []
            
            for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Collect tool calls (never shown to user)
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        if tc_delta.index is not None:
                            while len(tool_calls) <= tc_delta.index:
                                tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                            
                            if tc_delta.id:
                                tool_calls[tc_delta.index]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    tool_calls[tc_delta.index]["function"]["name"] = tc_delta.function.name
                                if tc_delta.function.arguments:
                                    tool_calls[tc_delta.index]["function"]["arguments"] += tc_delta.function.arguments
                
                # Stream text content immediately (unless previous tool was visible)
                if delta.content:
                    full_response += delta.content
                    if not last_tool_was_visible:
                        yield delta.content
            
            # If tool calls: execute them and loop
            if tool_calls:
                # Enforce single tool execution
                tool_calls_to_execute = tool_calls[:1] if len(tool_calls) > 1 else tool_calls
                executed_tool_name = tool_calls_to_execute[0]['function']['name']
                executed_tool_args = json.loads(tool_calls_to_execute[0]['function']['arguments'])
                
                # DEDUPLICATION CHECK: Has this exact tool been called before?
                tool_signature = _get_tool_signature(executed_tool_name, executed_tool_args)
                if tool_signature in tools_called_history:
                    # Add a system message to explain what happened
                    messages.append({
                        "role": "system",
                        "content": f"The tool '{executed_tool_name}' was already called with these exact arguments earlier in this conversation. The results are already available above. Please provide a final response to the user without calling this tool again."
                    })
                    
                    # Mark this tool as called so it won't be available next round
                    tools_called_names.add(executed_tool_name)
                    continue
                
                # Record this tool call signature and name
                tools_called_history.append(tool_signature)
                tools_called_names.add(executed_tool_name)
                
                # Add assistant message with tool call
                _add_assistant_message_with_tool_calls(messages, full_response, tool_calls_to_execute)
                
                # Execute tool and stream output
                for chunk in _execute_tool_calls(tool_calls_to_execute, messages):
                    yield chunk
                
                # Track if this tool was visible
                is_visible_tool = executed_tool_name in VISIBLE_TOOLS
                last_tool_was_visible = is_visible_tool
                
                # Loop again
                continue
            
            # No tool calls: we're done
            else:
                break
    
    except Exception as e:
        yield f"Error: {str(e)}"

