
class TracebackParser:
    def parse(self, traceback_text):
        lines = traceback_text.split("\n")
        result = {
            "files": [], 
            "exception": ""
        }
        for line in lines:
            if "File" in line:
                result["files"].append(line)
            if "Error" in line:
                result["exception"] = (line)
        return result