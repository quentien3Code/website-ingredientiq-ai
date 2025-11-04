**FoodAI backend Build and push commands**

Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888722447205.dkr.ecr.us-east-1.amazonaws.com
Note: if you receive an error using the AWS CLI, make sure that you have the latest version of the AWS CLI and Docker installed.
Build your Docker image using the following command. For information on building a Docker file from scratch, see the instructions here . You can skip this step if your image has already been built:
docker build -t foodai .
After the build is completed, tag your image so you can push the image to this repository:
docker tag foodai:latest 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest
Run the following command to push this image to your newly created AWS repository:
docker push 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest

<!-- docker buildx build --platform linux/amd64,linux/arm64 -t 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai:latest --push . (single command for build and push for MAC) -->

**FoodAI nginx commands to build and push**

Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI:
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 888722447205.dkr.ecr.us-east-1.amazonaws.com
Note: if you receive an error using the AWS CLI, make sure that you have the latest version of the AWS CLI and Docker installed.
Build your Docker image using the following command. For information on building a Docker file from scratch, see the instructions here . You can skip this step if your image has already been built:
docker build -t foodai-nginx ./nginx
After the build is completed, tag your image so you can push the image to this repository:
docker tag foodai-nginx:latest 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai-nginx:latest
Run the following command to push this image to your newly created AWS repository:
docker push 888722447205.dkr.ecr.us-east-1.amazonaws.com/foodai-nginx:latest


