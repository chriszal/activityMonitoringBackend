# from http import client
# import falcon, json
# import requests
# from requests.adapters import HTTPAdapter
# #from requests.packages.urllib3.util.retry import Retry
# from decouple import config
# import gzip
# from influxdb_client import InfluxDBClient, Point
# from influxdb_client.client.write_api import SYNCHRONOUS
# from concurrent.futures import ThreadPoolExecutor


# class MeasurementResource(object):
#     def __init__(self):
#         self.host = config('DOCKER_INFLUXDB_INIT_HOST')
#         self.port = config('DOCKER_INFLUXDB_INIT_PORT')
#         self.token= config('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
#         self.org = config('DOCKER_INFLUXDB_INIT_ORG')
#         self.bucket=config('DOCKER_INFLUXDB_INIT_BUCKET')
#         self.executor = ThreadPoolExecutor(max_workers=10)

#     def on_get(self, req, resp):
#         resp.status = falcon.HTTP_200

#     def on_post(self, req, resp):
#             try:
#                 # Open the gzip compressed file in binary mode
#                 with gzip.open(req.get_param('file').file, 'rb') as f:
#                     # Define a function to write data to InfluxDB
#                     def write_data(data):
#                         # Create an InfluxDBClient object
#                         client = InfluxDBClient(url=f"http://{self.host}:{self.port}", token=self.token)
#                         # Define the WriteApi object
#                         write_api = client.write_api(write_options=SYNCHRONOUS)

#                         # Use the write method to write the data to InfluxDB
#                         write_api.write(bucket=self.bucket, org=self.org, record=data)

#                         # Close the WriteApi object and InfluxDBClient object
#                         write_api.close()
#                         client.close()

#                     # Submit each file to the pool of workers to write data in parallel
#                     for file in f:
#                         self.executor.submit(write_data, file)

#                 resp.status = falcon.HTTP_204
#                 resp.body = json.dumps({
#                     'message': 'Data written to InfluxDB',
#                     'status': 204,
#                     'data': {}
#                 })
#             except Exception as e:
#                 resp.status = falcon.HTTP_400
#                 resp.body = json.dumps({
#                     'message': str(e),
#                     'status': 400,
#                     'data': {}
#                 })

import falcon, json
import requests
class MeasurementResource(object):


    def __init__(self,rabbitmq,INFLUXDB,logging):
        self.host = INFLUXDB['HOST']
        self.port = INFLUXDB['PORT']
        self.token = INFLUXDB['ADMIN_TOKEN']
        self.org = INFLUXDB['ORG']
        self.bucket = INFLUXDB['BUCKET']
        self.rabbitmq = rabbitmq
        self.logging = logging
        
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp):

        try:
            input_file = req.get_param('file')  
            self.rabbitmq.publish(message={"data": input_file.filename})
            response = requests.post(url="http://"+self.host+":"+self.port+"/api/v2/write?org="+self.org+"&bucket="+self.bucket+"&precision=ms",data=input_file.file,headers={'Content-Encoding':'gzip','Authorization':'Token '+self.token})
            self.logging.info(response)
            resp.status = falcon.HTTP_204

            resp.body = json.dumps({
                'message': str(response)+str(" | Time elapsed: ")+str(response.elapsed.total_seconds()),
                'status': 204,
                'data': str(response)
            })
        except Exception as e:
           
            resp.status = falcon.HTTP_400
            resp.body = json.dumps({
            'message': str(e),
            'status': 400,
            'data': {}
           })
            
