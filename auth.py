from dotenv import load_dotenv
load_dotenv()
def get_user_permissions(user_id):
    if user_id == "admin":
        return ["KB001", "KB002"]
    return ["KB001"]