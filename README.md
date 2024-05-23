FastAPI workflow for data-catalogue dockerized.

To run the data-catalogue workflow, make the following steps:

0. Create the network
   > docker network create _mynetwork_
2. Build the Dockerfile in src/Dockerfile:
   > docker build -t _data-catalogue-image_
3. Run the image:
   > docker run --network _mynetowrk_ --name _data-catalogue-container-name_ -p 8001:8001 _data-catalogue-image_
4. Go to http://localhost:8003/docs in your browser and return all datasets metadata available.
