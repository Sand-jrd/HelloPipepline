// ----  My first Jenking File --- //

pipeline {
// ----------------   EXECUION ENVIRONMENT    ---------------- //
    agent any

    stages {
								// ----------------   SOUCRE CODE    ---------------- //
								
	    stage('Clone sources') {
        		git url: 'https://github.com/Sand-jrd/CALSI-Projet-S8-.git'
		}
			
								// ----------------      BUILD       ---------------- //
        stage('Build') {
            steps {
                sh 'echo no build for now ...' 
            }
        }
    }
}
