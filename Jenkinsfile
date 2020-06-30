// ----  My first Jenking File --- //

pipeline {
// ----------------   EXECUION ENVIRONMENT    ---------------- //
    agent any

    stages {
								// ----------------   SOUCRE CODE    ---------------- //
								
	    stage('Clone sources') {
            steps {
              	git branch: 'master',
					credentialsId: 'f571a7e2-ea64-4d64-bdc9-e09ec8629466',
					url: 'https://github.com/Sand-jrd/CALSI-Projet-S8-.git'
            }
		    
       			 
		}
			
								// ----------------      BUILD       ---------------- //
        stage('Build') {
            steps {
                echo "no build for now"
            }
        }
    }
}
