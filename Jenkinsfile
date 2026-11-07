
pipeline {
    agent any

    environment {
        EC2_HOST = '16.176.155.23'
        REPO_URL = 'https://github.com/keerthipogul/AI-Fitness-Trainer.git'
        APP_DIR = 'AI-Fitness-Trainer-CI'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Update EC2 Project') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-ssh-key',
                        keyFileVariable: 'EC2_KEY',
                        usernameVariable: 'EC2_USER'
                    )
                ]) {
                    bat '''
                    icacls "%EC2_KEY%" /inheritance:r
                    icacls "%EC2_KEY%" /grant:r "*S-1-5-18:R"

                    ssh -i "%EC2_KEY%" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 %EC2_USER%@%EC2_HOST% "if [ -d AI-Fitness-Trainer-CI/.git ]; then cd AI-Fitness-Trainer-CI && git pull; else git clone %REPO_URL% AI-Fitness-Trainer-CI; fi"
                    '''
                }
            }
        }

        stage('Build Docker Image on EC2') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-ssh-key',
                        keyFileVariable: 'EC2_KEY',
                        usernameVariable: 'EC2_USER'
                    )
                ]) {
                    bat '''
                    icacls "%EC2_KEY%" /inheritance:r
                    icacls "%EC2_KEY%" /grant:r "*S-1-5-18:R"

                    ssh -i "%EC2_KEY%" %EC2_USER%@%EC2_HOST% "cd AI-Fitness-Trainer-CI && docker build -t ai-fitness-trainer:latest ."
                    '''
                }
            }
        }

        stage('Deploy on EC2') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-ssh-key',
                        keyFileVariable: 'EC2_KEY',
                        usernameVariable: 'EC2_USER'
                    )
                ]) {
                    bat '''
                    icacls "%EC2_KEY%" /inheritance:r
                    icacls "%EC2_KEY%" /grant:r "*S-1-5-18:R"

                    ssh -i "%EC2_KEY%" %EC2_USER%@%EC2_HOST% "docker rm -f ai-fitness-trainer || true"
                    ssh -i "%EC2_KEY%" %EC2_USER%@%EC2_HOST% "docker run -d --restart unless-stopped -p 8501:8501 --name ai-fitness-trainer ai-fitness-trainer:latest"
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'AI Fitness Trainer deployed successfully on AWS EC2!'
        }
        failure {
            echo 'Deployment failed. Check the Console Output.'
        }
    }
}
