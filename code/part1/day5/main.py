def flatten_json(json):
    def flatten(json) -> dict:
        current_json = {}
        if isinstance(json, dict):
            for k, v in json.items():
                if isinstance(v, dict):
                    current_json.update(flatten(v))
                else:
                    current_json[k] = v
        return current_json

    return flatten(json)
