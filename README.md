# GCP Kubernetes Deployment with Terraform

## Overview
Provisioned a Google Kubernetes Engine (GKE) cluster using
Terraform and deployed a containerized NGINX web server
using Kubernetes.

## Technologies
- Google Cloud Platform (GCP)
- Google Kubernetes Engine (GKE)
- Terraform
- Kubernetes
- NGINX
- Google Cloud CLI
- Linux

## Implementation
1. Enabled the required Google Cloud APIs.
2. Configured Terraform with the Google provider.
3. Provisioned a zonal GKE cluster and a one-node pool.
4. Created a Kubernetes Deployment manifest.
5. Deployed NGINX using kubectl.
6. Verified the Deployment and Pod were healthy.
7. Tested the application using kubectl port-forward.

## Verification
- Deployment: 1/1 available
- Pod: Running, 0 restarts
- HTTP response: 200 OK

## Cleanup
Remove infrastructure using terraform destroy.

## Notes
This is a learning project, not a production deployment.
GKE resources may incur cloud charges.
