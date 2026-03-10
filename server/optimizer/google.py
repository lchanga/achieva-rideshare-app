import os
from google.cloud import optimization_v1
from server.optimizer.base import Optimizer

class GoogleOptimizer(Optimizer):
    def __init__(self):
        self.client = optimization_v1.FleetRoutingClient()
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

    def optimize_tours(self, request_json: dict) -> dict:
        """
        Calls the Google Fleet Routing API.
        The request_json should match the OptimizeToursRequest message.
        """
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT_ID is not set.")

        request_json['parent'] = f"projects/{self.project_id}"
        
        try:

            request = optimization_v1.OptimizeToursRequest(request_json)
            response = self.client.optimize_tours(request=request)
            

            return optimization_v1.OptimizeToursResponse.to_dict(response)
        except Exception as e:
            raise Exception(f"Google Optimization API Error: {str(e)}")