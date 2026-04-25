from langgraph.checkpoint.memory import InMemorySaver

# TODO: make this some sort of custom checkpointer OR just use the sqlite saver. You can do this!
# Please please get it done I'll be super proud!
# https://docs.langchain.com/langsmith/custom-checkpointer
# - also want ToolMessageCreate and stuff, seamlessly interact with BaseMessage and all. Not sure its "neccessary but... yk"
#   - i think we only need to actually checkpoint the tool's output back to the AI, not the tools input!

checkpointer = InMemorySaver()
