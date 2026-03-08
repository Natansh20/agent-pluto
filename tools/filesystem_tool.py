import os

TEXT_LIMIT = 1000

def filesystem_tool(operation, path, content=None, file_type=None):
    if path in ["CWD", "cwd", ".", None]:
        path = os.getcwd()

    if operation == "view" or operation == "read":
        if os.path.isdir(path):
            try:
                return {
                    "status": "success",
                    "type": "directory",
                    "path": path,
                    "items": os.listdir(path)
                }
            except Exception as e:
                return {"status": "error", "message": f"Could not list directory: {str(e)}"}

        if os.path.isfile(path):
            try:
                with open(path, "r", errors="ignore") as f:
                    data = f.read(TEXT_LIMIT)
                return {
                    "status": "success",
                    "type": "file",
                    "path": path,
                    "preview": data
                }
            except Exception as e:
                return {"status": "error", "message": f"Could not read file: {str(e)}"}

    if operation == "create":
        with open(path, "w") as f:
            if content:
                f.write(content)
        return {
            "status": "success",
            "operation": "create",
            "path": path
            }

    if operation == "write":
        if path.endswith(".py"):
            with open(path, "w") as f:
                f.write(content)
        else:
            with open(path, "a") as f:
                f.write(content)

        return {
            "status": "success",
            "operation": "write",
            "path": path
            }          

    return {"error": "Unsupported filesystem operation"}
