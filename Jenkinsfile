// ----  My first Jenking File --- //

pipeline {
// ----------------   VARIABLES / ENVIRONMENT    ---------------- //
    agent any
	
 environment {
        def file_name_requirements = "serverless"
	def file_name = "serverlessExecutableJar"
    }	
	
    stages {

								
		stage('Clone sources') {
		    steps {
			git branch: 'master',
				credentialsId: 'f571a7e2-ea64-4d64-bdc9-e09ec8629466',
				url: 'https://github.com/Sand-jrd/CALSI-Projet-S8-.git'
		    }
		}

	    	/*
		stage ('Test 3: Master') {
			when { branch 'master' }
			steps { 
				echo 'I only execute on the master branch.' 
			}
		}
		*/
	    
		stage ('Checkout') {
			steps { 
				script {
					if (file_name.startsWith(file_name_requirements)) {
						echo 'Checkout sucess'
					} else {
						currentBuild.result = 'ABORTED'
    						error('Checkout failed')
					}
				}
			}
		}
			
		stage('Build') {
		    steps {
			echo "no build for now"
		    }
		}
    }
}
