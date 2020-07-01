// ----  My first Jenking File --- //

pipeline {
// ----------------   VARIABLES / ENVIRONMENT    ---------------- //
    agent any
	
 environment {
        def file_name_requirements = "serverless"
    }	
	
    stages {

								
	    stage('Clone sources') {
		    steps {
			git branch: 'master',
				credentialsId: 'f571a7e2-ea64-4d64-bdc9-e09ec8629466',
				url: 'https://github.com/Sand-jrd/CALSI-Projet-S8-.git'
		    }
	    }

	    // Trigger by jar deposit
	    stage('S3 Deploment') {
		    stage ('Test 3: Master') {
			    when { branch 'master' }
			    steps { 
				echo 'I only execute on the master branch.' 
			    }
			}

			stage ('Test 3: Dev') {
			    when { not { branch 'master' } }
			    steps {
				echo 'I execute on non-master branches.'
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
