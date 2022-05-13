from api import app, r
import unittest


class ApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.test_client()
        self.redis = r
        self.test_task_id = 1
        self.test_task_list = self.redis.lpush("task_list", self.test_task_id)
        self.test_task = self.redis.hset(self.test_task_id, mapping={"name": "test", "status": 0})

    def test_get_tasks(self):
        response = self.app.get("/tasks")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "result": [
                    {"id": task_id} | self.redis.hgetall(task_id) for task_id in self.redis.lrange("task_list", 0, -1)
                ]
            },
        )

    def test_post_task(self):
        test_json = {"name": "new_task"}
        response = self.app.post("/task", json=test_json)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, {"result": test_json | {"status": 0, "id": self.test_task_id + 1}})

    def test_put_task(self):
        test_json = {"name": "test", "status": 1}
        response = self.app.put(f"/task/{self.test_task_id}", json=test_json)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"result": test_json | {"id": self.test_task_id}})
        # test 400 for id not exists
        response = self.app.put("/task/2", json=test_json)
        self.assertEqual(response.status_code, 400)

    def test_delete_task(self):
        response = self.app.delete(f"/task/{self.test_task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.test_task_id in self.redis.lrange("task_list", 0, -1))
        self.assertFalse(self.redis.exists(self.test_task_id))
        # test 400 for id not exists
        response = self.app.put("/task/2")
        self.assertEqual(response.status_code, 400)

    def tearDown(self) -> None:
        for task_id in self.redis.lrange("task_list", 0, -1):
            self.redis.delete(task_id)
        self.redis.delete("task_list")


if __name__ == "__main__":
    unittest.main()
