from locust import HttpUser, task

class testUser (HttpUser):

    @task
    def refresh(self):
        self.client.get("/")


    @task(15)
    def get_quote(self):
        self.client.get("/random-quote")

    
    @task(8)
    def get_all_quotes(self):
        self.client.get("/quotes")

    @task
    def add_quote(self):
        self.client.post("/add-quote", json={"quote":"test - locust"})