pipeline {
    agent any
    
    environment {
        // Configurable via Jenkins credentials / variables
        REGISTRY = 'flowershop.azurecr.io'
        IMAGE_NAME = 'banking-app'
        IMAGE = "${REGISTRY}/${IMAGE_NAME}"
        TAG = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'latest'}"
        
        // Azure / ACI deployment environment variables
        RESOURCE_GROUP = 'qr-payment-rg'
        ACI_GROUP_NAME = 'qr-payment-test-group'
        
        // Target URLs for testing
        TEST_URL = 'http://test-bank.nip.io'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build & Unit Test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install -r requirements.txt
                    pytest
                '''
            }
        }
        
        stage('Docker Build & Push') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'acr-credentials', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS')]) {
                    sh '''
                        docker login ${REGISTRY} -u ${REG_USER} -p ${REG_PASS}
                        docker build -t ${IMAGE}:${TAG} -t ${IMAGE}:latest .
                        docker push ${IMAGE}:${TAG}
                        docker push ${IMAGE}:latest
                    '''
                }
            }
        }
        
        stage('Deploy to Test (ACI)') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'azure-service-principal', usernameVariable: 'AZURE_CLIENT_ID', passwordVariable: 'AZURE_CLIENT_SECRET')]) {
                    sh '''
                        # Login to Azure using Service Principal
                        az login --service-principal -u ${AZURE_CLIENT_ID} -p ${AZURE_CLIENT_SECRET} --tenant ${AZURE_TENANT_ID}
                        
                        # Execute ACI deployment script
                        chmod +x ./deploy/aci-deploy.sh || true
                        ./deploy/aci-deploy.sh ${IMAGE}:${TAG}
                    '''
                }
            }
        }
        
        stage('Smoke Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest tests/smoke --base-url=${TEST_URL}
                '''
            }
        }
        
        stage('Approve Prod Deploy') {
            steps {
                input message: 'Approve deployment to Production (AKS/EKS)?', ok: 'Deploy to Prod'
            }
        }
        
        stage('Deploy to Prod (K8s)') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig-prod', variable: 'KUBECONFIG')]) {
                    sh '''
                        # Set image on the Kubernetes deployment
                        kubectl --kubeconfig=$KUBECONFIG set image deployment/banking-app-deployment banking-app-container=${IMAGE}:${TAG}
                        # Verify rollout status
                        kubectl --kubeconfig=$KUBECONFIG rollout status deployment/banking-app-deployment
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
