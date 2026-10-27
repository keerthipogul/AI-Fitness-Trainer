
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t ai-fitness-trainer:latest .'
            }
        }

        stage('Deploy Container') {
            steps {
                bat 'docker compose up -d'
            }
        }
    }

    post {
        success {
            echo 'AI Fitness Trainer deployed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
    }
}
