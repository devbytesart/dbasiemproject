""" 
Copyright 2026 ttdantett DevBytesArt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

author: ttdantett
title: siem project
document: ai_commands
"""

import traceback
from typing import Any
from UtilsCrypto import *
import json
import requests
import time
import re
import uuid

##############################################################
###     LLM QUERIES COMMANDS
##############################################################


def ai_llm_query_ollama(self: Any, instance: str, query: str, model: str = "qwen2.5:14b", https: bool = False, temperature: float = 0.2):
    """
    Simple Query/Answer to the LLM
    - instance: str => SOAR Instance that contains the credentials and urls to reach the LLM
    - query: str => User query to the LLM
    - model: str (qwen2.5:14b) => LLM Model installed on ollama
    """
    try:
        if instance is not None and query is not None:
            # Get instance credentials
            credentials = self.vault.get(instance)
            url = credentials.get("url")
            api_key = credentials.get("apikey", "")
            # Protocol definition
            protocol = "https" if https else "http"
            endpoint = f"{protocol}://{url.rstrip('/')}/api/chat"
            print(endpoint)
            # Header configuration
            headers = {"Content-Type": "application/json"}
            if api_key != "":
                headers["Authorization"] = f"Bearer {api_key}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": query}
                ],
                "options" : {
                    "temperature": temperature
                },
                "stream": False  
            }
            print("payload:", str(payload))
            # Send request
            try:
                response = requests.post(endpoint, json=payload, headers=headers)
                print("response:", str(response.content))
            except Exception as e:
                self.logger.log("error", f"SOAR AI LLM Query network error: {traceback.format_exc()}")
                raise e
            # Handle response
            if response.status_code == 200:
                print(response.content)
                return str(response.json()["message"]["content"])
            else:
                error_msg = f"Ollama returned status {response.status_code}: {response.text}"
                self.logger.log("error", error_msg)
                return f"Error: {error_msg}"
    except Exception as main_exception:
        self.logger.log("error", f"SOAR AI LLM Query global error: {traceback.format_exc()}")
        raise main_exception



##############################################################
###      AGENTIC COMMANDS
##############################################################

# def ai_agentic_query_ollama(self: Any, instance: str, query:str, tenant: str, index: str = "soar", model: str = "qwen2.5:14b", https: bool = False, session_token: str = None):
#     """
#     The LLM received the query with this command and create wrokplan and launch action on the SOAR
#     - instance: str => SOAR Instance that contains the credentials and urls to reach the LLM
#     - query: str => User query to the LLM
#     - model: str => LLM Model installed on ollama (qwen2.5:14b)
#     - session_token: str => Token of the user (None)
#     - index: str => index to save the context (soar)
#     - tenant: str => tenant where to save the context
#     """
#     try:
#         context_name = "agentic"
#         print("BEFORE COMMANDS LIST")
#         #commands_list = self.commands["soar_set_context"]["function"]("testagentic2", "soar", "siem_system", "soar_get_help", params={"filter":""}, author="soar", session_token=session_token, display=False)
#         commands_list = []
#         for com in self.commands.keys():
#             # TODO erase this next part, temporary
#             commands_list.append({
#                 "name": com,
#                 "description": str(self.commands[com]["description"]),
#                 "params": str(self.commands[com]["params"])
#             })
#         print("AFTER COMMAND LIST", str(commands_list)[:50])
#         #Prepare LLM
#         instructions = """
#             You are an intelligent orchestrator (SOAR). Your goal is to assist the user by answering their questions or executing specific actions. To achieve this, you have access to a list of functions (tools) that you can decide to call.

#             Here is the list of available functions, their parameters, and descriptions:
#             """ + str(commands_list).replace("\"","").replace("\'","").replace("\\","") + """
#             ---

#             ### DECISION RULES
#             1. If you can accurately answer the user's question WITHOUT using any function (to save time), do so directly.
#             2. If the user's request requires an action or information that you do not possess, you MUST select and configure the appropriate function(s) from the list above.
#             3. Do not guess parameters. Extract them from the ongoing context provided in the available functions before. If a required parameter is missing, ask the user for it via the "text" field.
#             5. **siem_search** The siem_search is the command from the SIEM These example below are only for parameter query, other parameters are explained before in the list of availables commands. Use pipe to separate operations and ! for the command. See example below:
#             - !search * | !counts by <field> | !order by <field> | !render <chart type> by <field> over count
#             - !search <condition1> and <condition2> or <condition3> | !order by <field>
#             - !search <condition> | !transform <field> as substring(:5) | !counts by <field>_substring5
            
#             ### MANDATORY OUTPUT FORMAT
#             You must strictly respond using the following UNIQUE JSON format. Do not include any conversational text outside the JSON, and do not use Markdown code blocks (do not wrap it in ```json ... ```). Provide the raw JSON only:

#             {
#             "text": ["Step 1 or message to the user", "Step 2..."],
#             "function": [
#                 {
#                 "name": "function_name",
#                 "parameters": {
#                     "param1": "value1",
#                     "param2": "value2"
#                 }
#                 }
#             ],
#             "result": null
#             }

#             ### HOW TO HANDLE RESULTS ("result")
#             - When you request a function execution, the external script will run it and send this exact same JSON back to you, but the "result" field will contain the data returned by the function.
#             - When you receive a JSON where the "result" field is no longer "null" but contains data, your role is to analyze this data to formulate the final answer to the user inside the "text" field, and clear the "function" field (set it to []).

#             ### USER REQUEST
#             The following request has been done by the user, answer this question :
#             """ + query


#         print("Send request and instructions to the llm")
#         results = self.commands["soar_set_context"]["function"](context_name, index, tenant, "ai_llm_query_ollama", params={"query":instructions,"instance":instance}, author="soar", session_token=session_token)
#         print("RESULT LLM:",str(results))
#         time.sleep(5)
#         #Launch the commands
#         print("FUNCTION: ", str(json.loads(results["history"][0]["answer"][0])["function"]))
#         for func in json.loads(results["history"][0]["answer"][0])["function"]:
#             try:
#                 print("FUNCTION NAME:", str(type(func["name"])), str(func["name"]))
#                 print("FUNCTION PARAMETERS:", str(type(func["parameters"])), str(func["parameters"]))
#                 self.commands["soar_set_context"]["function"](context_name, index, tenant, func["name"], params=func.get("parameters",{}),  author="soar", session_token=session_token)
#             except:
#                 self.logger.log("error",f"Error during launch function {func['name']} {traceback.format_exc()}")
#         # # Function to find answer keys
#         # def find_keys(data, target_key):
#         #     results = []
#         #     # Si c'est un dictionnaire, on cherche la clé et on fouille dans les valeurs
#         #     if isinstance(data, dict):
#         #         for key, value in data.items():
#         #             if key == target_key:
#         #                 results.append(value)
#         #             # On continue de chercher plus profondément dans la valeur
#         #             results.extend(find_keys(value, target_key))
#         #     # Si c'est une liste, on fouille dans chaque élément de la liste
#         #     elif isinstance(data, list):
#         #         for item in data:
#         #             results.extend(find_keys(item, target_key))
#         #     return results
#         # # If any value is required by the LLM to answer the question
#         # try:
#         #     res = find_keys(self.context, "answer")
#         #     results = json.loads(results["history"][0]["answer"][0])
#         #     results["result"] = str(res)
#         #     print("RESULTS TO SEND TO LLM", str(results))
#         #     self.commands["soar_set_context"]["function"](context_name, index, tenant, "ai_llm_query_ollama", params={"query":results,"instance":instance}, author="soar", session_token=session_token)
#         # except:
#         #     self.logger.log("error",f"Error during request to llm {traceback.format_exc()}")
#         return "ok"
#         # TODO to continue
#     except Exception as main_exception:
#         self.logger.log("error", f"SOAR AI Agentic Query global error: {traceback.format_exc()}")
#         raise main_exception



def ai_agentic_query_ollama(self, instance: str, query: str, tenant: str, index: str = "soar",
                             model: str = "qwen2.5:14b", https: bool = False, session_token: str = None,
                             max_turns: int = 5, max_duration_seconds: int = 120):
    """
    The LLM receives the request, decides on an action plan, and exchanges messages with the
    SOAR until it reaches a final answer. How it works:
      1. Only the commands relevant to the request are built and sent to the LLM
         (keyword filtering, see _select_relevant_commands), not the full list.
         A "meta" tool (get_command_details) is always available so the LLM can request
         extended documentation for ONE specific command, only when it actually needs it.
      2. The prompt is sent via soar_set_context / ai_llm_query_ollama.
      3. If the LLM requests functions, they are executed (each one wrapped in its own
         try/except so a single failure never blocks the other calls or the tool). An
         empty result is NOT an error: that's normal, the LLM can adjust and retry.
      4. Only the result of those functions is sent back to the LLM (not the full command
         list again, which is already known from the conversation context) so it can decide
         what to do next.
      5. The loop continues until the LLM stops requesting functions, until max_turns is
         reached (safety net against infinite loops), or until the exact same call
         (name + parameters) is detected MAX_REPEATED_CALLS times in a row.

    - instance: str => SOAR instance holding the credentials and URLs to reach the LLM
    - query: str => User request sent to the LLM
    - model: str => LLM model installed on ollama (qwen2.5:14b)
    - session_token: str => User token (None)
    - index: str => index where the context is saved (soar)
    - tenant: str => tenant where the context is saved
    - max_turns: int => maximum number of round trips with the LLM (safety net against infinite loops)
    - max_duration_seconds: int => hard wall-clock timeout for the whole exchange, in addition to
      max_turns (safety net in case a single call takes an unexpectedly long time)
    """
    # --- Local constants (everything is scoped inside the function, nothing at module level) ---
    TOP_K_COMMANDS = 8         # max number of commands sent to the LLM (instead of all of them)
    LLM_POLL_DELAY = 5         # seconds to wait after calling the LLM (ideally replace with polling/callback)
    MAX_REPEATED_CALLS = 2     # if the LLM asks for the EXACT same call (name+params) this many times in a row, stop

    # Reserved name for the "meta" tool that lets the LLM request detailed documentation
    # for a specific command, on demand, without bloating the initial prompt.
    GET_DETAILS_TOOL_NAME = "get_command_details"

    # Extended documentation per command. This dictionary can grow freely (as many commands
    # as needed) without ever making the base prompt heavier: it is only sent to the LLM if
    # it explicitly requests it via GET_DETAILS_TOOL_NAME.
    COMMAND_DETAILS = {
        "siem_search": (
            "DETAILED DOCUMENTATION - siem_search\n\n"
            "The syntax uses operations separated by pipes (|), executed in the STRICT order "
            "in which they are written, left to right. THE ORDER MATTERS: each operation works "
            "on the output of the previous one.\n\n"
            "Mandatory rule: a !render that displays numeric values (bars, lines, pie charts, "
            "etc.) must ALWAYS be preceded by a !counts (or an equivalent aggregation) in the "
            "same query. Without a !counts before it, there are no numeric values to display "
            "and the render will be empty or invalid.\n\n"
            "Correct examples:\n"
            "- !search * | !counts by <field> | !order by <field> | !render <chart type> by <field> over count\n"
            "- !search <condition1> and <condition2> or <condition3> | !order by <field>\n"
            "- !search <condition> | !transform <field> as substring(:5) | !counts by <field>_substring5\n\n"
            "INCORRECT example (render without counts before it, avoid this):\n"
            "- !search * | !render bar by <field>   <-- missing !counts before !render, this will not work"
        ),
    }

    def _tokenize(text: str):
        """Tokenize a text into simple words (lowercase, alphanumeric + underscore)."""
        return re.findall(r"[a-zA-Z0-9_]+", str(text).lower())

    def _score_command(query_tokens, command: dict) -> int:
        """
        Simple relevance score (common words) between the user query and a command.

        This acts as a lightweight "RAG" step with no external dependency: it only compares
        tokens. If you have an embeddings model available via Ollama (the /api/embeddings
        endpoint), replace this function with a cosine similarity computation between the
        query vector and each command's vector (pre-computed and cached) for finer-grained
        filtering.
        """
        text = f"{command.get('name', '')} {command.get('description', '')} {command.get('params', '')}"
        command_tokens = _tokenize(text)
        if not command_tokens:
            return 0
        return len(set(query_tokens) & set(command_tokens))

    def _select_relevant_commands(query_: str, commands_list: list, top_k: int = TOP_K_COMMANDS) -> list:
        """
        Select only the commands relevant to the query, instead of sending the full list to
        the LLM. This shrinks the prompt, speeds up the response, and reduces the LLM's
        chances of picking the wrong function.
        """
        query_tokens = _tokenize(query_)
        scored = [(_score_command(query_tokens, cmd), cmd) for cmd in commands_list]
        scored.sort(key=lambda x: x[0], reverse=True)

        selected = [cmd for score, cmd in scored if score > 0][:top_k]

        # Safety net: if no keyword matches at all, still send a minimal baseline of
        # commands rather than leaving the LLM with no tools at all.
        if not selected:
            selected = commands_list[:top_k]

        return selected

    def _build_instructions(commands_list, payload: str, is_followup: bool = False) -> str:
        """
        Build the prompt sent to the LLM.
        - is_followup=False: first turn, contains the filtered command list + the user question.
        - is_followup=True:  following turns, contains ONLY the result of the executed functions
                              (not the command list again, already known from the conversation context).
        """
        if not is_followup:
            tools_str = str(commands_list).replace('"', "").replace("'", "").replace("\\", "")

            # The "get_command_details" tool is always offered, even if it wasn't picked up by
            # the keyword filter: it only costs a few words in the prompt, and it lets the LLM
            # request extended documentation for ONE specific command, only when it needs it
            # (instead of receiving everything at once).
            meta_tool_str = (
                "{name: " + GET_DETAILS_TOOL_NAME + ", "
                "description: Returns detailed documentation, syntax rules and examples for ONE specific "
                "command. Call this ONLY for a command you are unsure how to use correctly before using it "
                "- do not call it for every command., "
                "params: {command_name: name of the command you want details about}}"
            )

            return (
                "You are an intelligent orchestrator (SOAR). Your goal is to assist the user by answering "
                "their questions or executing specific actions. To achieve this, you have access to a list "
                "of functions (tools) that you can decide to call.\n\n"
                "Here is the list of available functions, their parameters, and descriptions "
                "(only the ones relevant to this request):\n"
                + tools_str + "\n"
                + meta_tool_str + "\n"
                "---\n\n"
                "### DECISION RULES\n"
                "1. If you can accurately answer the user's question WITHOUT using any function "
                "(to save time), do so directly.\n"
                "2. If the user's request requires an action or information that you do not possess, "
                "you MUST select and configure the appropriate function(s) from the list above.\n"
                "3. Do not guess parameters. Extract them from the ongoing context provided before. "
                "If a required parameter is missing, ask the user for it via the \"text\" field.\n"
                "4. If you are not fully sure about the exact syntax or rules of a command, call "
                + GET_DETAILS_TOOL_NAME + " with that command's name FIRST, instead of guessing. "
                "Only request details for the command(s) you actually need - never all of them at once.\n"
                "5. **siem_search** IMPORTANT: the order of operations in a !search query matters, they run "
                "strictly left to right, each one working on the output of the previous one. A !render that "
                "shows numeric values MUST always be preceded by a !counts (or equivalent aggregation) in the "
                "same query - otherwise there are no numeric values to render and it will fail or be empty. "
                "Use pipe to separate operations and ! for the command. See examples below:\n"
                "- !search * | !counts by <field> | !order by <field> | !render <chart type> by <field> over count\n"
                "- !search <condition1> and <condition2> or <condition3> | !order by <field>\n"
                "- !search <condition> | !transform <field> as substring(:5) | !counts by <field>_substring5\n"
                "If you need more detail on siem_search or any other command, call " + GET_DETAILS_TOOL_NAME
                + " rather than guessing.\n"
                "6. An empty or \"no result\" answer from a function is NOT an error - it simply means the "
                "search/action found nothing. Feel free to adjust and relaunch the command(s) with different "
                "parameters if needed, it is a normal part of the process.\n\n"
                "### MANDATORY OUTPUT FORMAT\n"
                "You must strictly respond using the following UNIQUE JSON format. Do not include any "
                "conversational text outside the JSON, and do not use Markdown code blocks. Provide the raw "
                "JSON only:\n\n"
                "{\n"
                "\"text\": [\"Step 1 or message to the user\", \"Step 2...\"],\n"
                "\"function\": [\n"
                "    {\n"
                "    \"name\": \"function_name\",\n"
                "    \"parameters\": {\n"
                "        \"param1\": \"value1\",\n"
                "        \"param2\": \"value2\"\n"
                "    }\n"
                "    }\n"
                "],\n"
                "\"result\": null\n"
                "}\n\n"
                "### HOW TO HANDLE RESULTS\n"
                "- When you request a function execution, you will receive back only the result of that "
                "execution (not the full function list again).\n"
                "- Analyze that result and either request another function call, or, if you have enough "
                "information, provide the final answer in \"text\" and set \"function\" to [].\n\n"
                "### USER REQUEST\n" + payload
            )
        else:
            return (
                "Here is the result of the function(s) you requested previously.\n\n"
                "### RULES\n"
                "- Analyze this result against the user's original request.\n"
                "- If another action is needed, respond using the same strict JSON format, filling in "
                "\"function\".\n"
                "- If you have enough information, write the final answer in \"text\" and leave "
                "\"function\": [].\n"
                "- Never return text outside the JSON, or a Markdown code block.\n\n"
                "### RESULT(S)\n" + payload
            )

    # A shared, static context_name would be overwritten/interleaved by concurrent or
    # successive calls (multiple users, multiple requests), which can make the agent look
    # like it is stuck in an infinite loop while it is actually reading someone else's
    # conversation history. Each invocation gets its own isolated context.
    context_name = f"agentic_{uuid.uuid4().hex[:8]}"
    start_time = time.monotonic()

    self.logger.log("debug", f"[{context_name}] Starting agentic run - query: {query!r}")

    # --- 1. Build the list of available commands ---
    try:
        commands_list = [
            {
                "name": com,
                "description": str(self.commands[com]["description"]),
                "params": str(self.commands[com]["params"]),
            }
            for com in self.commands.keys()
        ]
    except Exception:
        self.logger.log("error", f"Unable to list available commands: {traceback.format_exc()}")
        return "error"

    # --- 2. Lightweight RAG filtering: keep only the commands relevant to the query ---
    try:
        relevant_commands = _select_relevant_commands(query, commands_list, TOP_K_COMMANDS)
        self.logger.log(
            "info",
            f"Commands selected for the LLM ({len(relevant_commands)}/{len(commands_list)}): "
            f"{[c['name'] for c in relevant_commands]}"
        )
    except Exception:
        self.logger.log("error", f"Error while filtering commands: {traceback.format_exc()}")
        relevant_commands = commands_list[:TOP_K_COMMANDS]

    turn_query = _build_instructions(relevant_commands, query, is_followup=False)
    final_text = None
    last_call_signature = None
    repeated_calls_count = 0

    # --- 3. Bidirectional exchange loop with the LLM ---
    for turn in range(max_turns):

        elapsed = time.monotonic() - start_time
        if elapsed > max_duration_seconds:
            self.logger.log(
                "warning",
                f"[{context_name}] Wall-clock timeout reached ({elapsed:.1f}s > {max_duration_seconds}s), stopping the agent."
            )
            break

        self.logger.log("debug", f"[{context_name}] Turn {turn}: calling the LLM (elapsed={elapsed:.1f}s)")

        try:
            results = self.commands["soar_set_context"]["function"](
                context_name, index, tenant, "ai_llm_query_ollama",
                params={"query": turn_query, "instance": instance},
                author="soar", session_token=session_token
            )
        except Exception:
            self.logger.log("error", f"[{context_name}] Error calling the LLM (turn {turn}): {traceback.format_exc()}")
            break

        self.logger.log("debug", f"[{context_name}] Turn {turn}: LLM call returned, waiting {LLM_POLL_DELAY}s")
        time.sleep(LLM_POLL_DELAY)

        try:
            # Read the LAST entry of this context's history, not the first: with a shared/reused
            # context, index 0 can point to an old or unrelated message and make the agent appear
            # stuck by re-processing stale data forever.
            raw_answer = results["history"][-1]["answer"][-1]
            llm_response = json.loads(raw_answer)
        except Exception:
            self.logger.log("error", f"[{context_name}] Invalid or unparsable LLM response (turn {turn}): {traceback.format_exc()}")
            break

        final_text = llm_response.get("text", final_text)
        functions_to_run = llm_response.get("function", []) or []
        self.logger.log("debug", f"[{context_name}] Turn {turn}: LLM requested functions: {[f.get('name') for f in functions_to_run]}")

        if not functions_to_run:
            # The LLM no longer needs to run any function: we have the final answer
            break

        # --- Anti infinite-loop safeguard: is the LLM requesting EXACTLY the same call
        #     (same name + same parameters) as the previous turn? ---
        try:
            call_signature = json.dumps(functions_to_run, sort_keys=True, default=str)
        except Exception:
            call_signature = str(functions_to_run)

        if call_signature == last_call_signature:
            repeated_calls_count += 1
        else:
            repeated_calls_count = 0
        last_call_signature = call_signature

        if repeated_calls_count >= MAX_REPEATED_CALLS:
            self.logger.log(
                "warning",
                f"Loop detected: the LLM requested the same call {repeated_calls_count + 1} times in a row, stopping the agent."
            )
            break

        # --- 4. Execute the requested functions, each isolated in its own try/except ---
        execution_results = []
        for func in functions_to_run:
            func_name = func.get("name")
            func_params = func.get("parameters", {})
            self.logger.log("debug", f"[{context_name}] Turn {turn}: executing {func_name} with {func_params}")

            # Special case: request for detailed documentation about a command.
            # This is not a real SOAR command, so it does not go through self.commands.
            if func_name == GET_DETAILS_TOOL_NAME:
                try:
                    requested_command = func_params.get("command_name", "")
                    details = COMMAND_DETAILS.get(
                        requested_command,
                        f"No detailed documentation available for '{requested_command}'."
                    )
                    execution_results.append({
                        "name": func_name,
                        "parameters": func_params,
                        "result": details,
                    })
                except Exception:
                    self.logger.log("error", f"Error while retrieving detailed documentation: {traceback.format_exc()}")
                    execution_results.append({
                        "name": func_name,
                        "parameters": func_params,
                        "error": "execution failed",
                    })
                continue

            try:
                func_result = self.commands["soar_set_context"]["function"](
                    context_name, index, tenant, func_name,
                    params=func_params, author="soar", session_token=session_token
                )
                # An empty result is not an error: it is passed back to the LLM as-is,
                # which can decide to retry the command with different parameters.
                execution_results.append({
                    "name": func_name,
                    "parameters": func_params,
                    "result": func_result,
                })
            except Exception:
                self.logger.log("error", f"Error while executing function {func_name}: {traceback.format_exc()}")
                execution_results.append({
                    "name": func_name,
                    "parameters": func_params,
                    "error": "execution failed",
                })

        # --- 5. Only the result of the functions is sent back to the LLM, not the full command list ---
        try:
            payload = json.dumps(execution_results, default=str)
        except Exception:
            payload = str(execution_results)

        turn_query = _build_instructions(None, payload, is_followup=True)

    else:
        self.logger.log("warning", f"[{context_name}] Maximum number of turns ({max_turns}) reached for this agentic request.")

    total_elapsed = time.monotonic() - start_time
    self.logger.log("debug", f"[{context_name}] Agentic run finished in {total_elapsed:.1f}s")

    return final_text or "ok"