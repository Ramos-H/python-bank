pipeline {
    agent any

    environment {
        // Secret Text credentials
        REGISTRY       = credentials('acr-registry')
        IMAGE_NAME     = credentials('bank-image-name')
        RESOURCE_GROUP = credentials('azure-resource-group')
        ACI_GROUP_NAME = credentials('bank-aci-group-name')
        TEST_URL       = credentials('bank-test-url')

        IMAGE = "${REGISTRY}/${IMAGE_NAME}"
        TAG   = "${env.GIT_COMMIT ? env.GIT_COMMIT.take(7) : 'latest'}"
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
                '''
            }
        }

        stage('Docker Build & Push') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'azure-service-principal',
                        usernameVariable: 'AZURE_CLIENT_ID',
                        passwordVariable: 'AZURE_CLIENT_SECRET'
                    ),
                    string(
                        credentialsId: 'azure-tenant-id',
                        variable: 'AZURE_TENANT_ID'
                    )
                ]) {
                    sh '''
                        # Login to Azure using Service Principal
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}

                        # Extract ACR name from registry URL
                        ACR_NAME=$(echo ${REGISTRY} | cut -d'.' -f1)

                        # Login to Azure Container Registry
                        az acr login --name ${ACR_NAME} --expose-token

                        # Build Docker image
                        docker build \
                            -t ${IMAGE}:${TAG} \
                            -t ${IMAGE}:latest .

                        # Push images
                        docker push ${IMAGE}:${TAG}
                        docker push ${IMAGE}:latest
                    '''
                }
            }
        }

        stage('Deploy to Test (ACI)') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'azure-service-principal',
                        usernameVariable: 'AZURE_CLIENT_ID',
                        passwordVariable: 'AZURE_CLIENT_SECRET'
                    ),
                    string(
                        credentialsId: 'azure-tenant-id',
                        variable: 'AZURE_TENANT_ID'
                    )
                ]) {
                    sh '''
                        # Login to Azure using Service Principal
                        az login --service-principal \
                            -u ${AZURE_CLIENT_ID} \
                            -p ${AZURE_CLIENT_SECRET} \
                            --tenant ${AZURE_TENANT_ID}

                        # Execute ACI deployment script
                        chmod +x ./deploy/aci-deploy.sh || true
                        ./deploy/aci-deploy.sh ${IMAGE}:${TAG}
                    '''
                }
            }
        }

        // stage('Smoke Test') {
        //     steps {
        //         sh '''
        //             . .venv/bin/activate

        //             # Example smoke test
        //             curl -f ${TEST_URL} || exit 1
        //         '''
        //     }
        // }

        stage('Approve Prod Deploy') {
            steps {
                input(
                    message: 'Approve deployment to Production (AKS/EKS)?',
                    ok: 'Deploy to Prod'
                )
            }
        }

        stage('Deploy to Prod (K8s)') {
            steps {
                withCredentials([
                    file(
                        credentialsId: 'bank-kubeconfig-prod',
                        variable: 'KUBECONFIG'
                    )
                ]) {
                    sh '''
                        # Set image on the Kubernetes deployment
                        kubectl --kubeconfig=$KUBECONFIG \
                            set image deployment/banking-app-deployment \
                            banking-app-container=${IMAGE}:${TAG}

                        # Verify rollout status
                        kubectl --kubeconfig=$KUBECONFIG \
                            rollout status deployment/banking-app-deployment
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