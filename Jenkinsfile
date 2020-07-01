// ----  My first Jenking File --- //

pipeline {
// ----------------   VARIABLES / ENVIRONMENT    ---------------- //
    agent any
	
 environment {
        def file_name_requirements = "serverless"
	def file_name = "false"
	def file_ex = "false"
    }	
	
    stages {

								
		stage('Clone sources') {
		    steps {
			    
			// Clone from git
			git branch: 'master',
				credentialsId: 'f571a7e2-ea64-4d64-bdc9-e09ec8629466',
				url: 'https://github.com/Sand-jrd/SampleApplicationWar.git'
			    
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
					
					def files = findFiles glob: '*.war'
					
					//Check
					files.each { item ->
						if (item.name.startsWith(file_name_requirements)) {
							file_name = item.name;
							echo 'Checkout sucess'
						} else {
							currentBuild.result = 'ABORTED'
							error('Checkout failed')
						}
					}
				}
			}
		}
			
		stage('Bucket Transition') {
		    steps {
			echo "no build for now"
		    }
		}
    }
}
