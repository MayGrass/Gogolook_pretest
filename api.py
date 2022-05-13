from flask import Flask
from flask_restful import Api, Resource, reqparse
import redis
from environs import Env

env = Env()
env.read_env()


r = redis.StrictRedis(
    host=env.str("DB_SERVER"), port=env.int("DB_PORT"), db=env.int("DB"), charset="utf-8", decode_responses=True
)  # connect to redis

app = Flask(__name__)

api = Api(app)

parser = reqparse.RequestParser()

static_response = {"result": None}
error_response = {"error": None}


class Tasks(Resource):
    def get(self):
        task_list = r.lrange("task_list", 0, -1)
        static_response["result"] = [{"id": task_id} | r.hgetall(task_id) for task_id in task_list]
        return static_response


class Task(Resource):
    # 初始化陣列
    def init_task_list(self):
        if not r.exists("task_list"):
            return r.lpush("task_list", 1)

    def post(self):
        parser.add_argument("name", type=str, location="json")
        args = parser.parse_args()
        print(f"{args=}")
        try:
            # id遞增
            new_id = int(r.lrange("task_list", 0, -1)[-1]) + 1
            r.rpush("task_list", new_id)
        except:
            new_id = self.init_task_list()
        finally:
            data = {"name": args["name"], "status": 0}
            r.hset(new_id, mapping=data)
            print(f'{r.lrange("task_list", 0, -1)=}')
            static_response["result"] = data | {"id": new_id}
        return static_response, 201


class ModifyTask(Resource):
    def put(self, task_id):
        print(f"{task_id=}")
        if not r.exists(task_id):
            error_response["error"] = "task_id not exists"
            return error_response, 400
        parser.add_argument("name", type=str, location="json")
        parser.add_argument("status", type=int, location="json")
        args = parser.parse_args()
        print(f"{args=}")
        status_dict = {1: True, 0: False}
        if status_dict.get(args["status"]) is None:
            error_response["error"] = "status only allow 1 or 0"
            return error_response, 400
        r.hset(task_id, mapping=args)
        static_response["result"] = args | {"id": task_id}
        return static_response

    def delete(self, task_id):
        print(f"{task_id=}")
        if not r.exists("task_list"):
            error_response["error"] = "task_id not exists"
            return error_response, 400
        r.lrem("task_list", 0, str(task_id))
        print(f'{r.lrange("task_list", 0, -1)=}')
        r.delete(task_id)


api.add_resource(Tasks, "/tasks")
api.add_resource(Task, "/task")
api.add_resource(ModifyTask, "/task/<int:task_id>")

if __name__ == "__main__":
    app.run(host=env.str("HOST"), debug=env.bool("DEBUG"))
