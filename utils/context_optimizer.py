from config import MAX_CONTEXT_LENGTH


def optimize_context(results):
    context = ""
    for item in results:
        content = item["content"]

        if len(context) + len(content) > MAX_CONTEXT_LENGTH:
            break

        context += "\n\n"
        context += f"FILE : {item['file_name']}\n"
        context += content

    return context