// ----  My first Jenking File --- //

pipeline {
// ----------------   VARIABLES / ENVIRONMENT    ---------------- //
    agent any
	
 environment {
        
	// PATHS
	def SRC_URL = "https://github.com/Sand-jrd/SampleApplicationWar.git"
	def SRC_ID = "f571a7e2-ea64-4d64-bdc9-e09ec8629466"
	def SERVER_PATH = "C:/Program Files/Apache Software Foundation/Tomcat 8.5/webapps"
	// CHECKOUT PARAMETERS
	def file_name_requirements = "serverless"
	def file_cond = "*.war"
	// GLOBAL VARIABLE DECLARATION
	def file_name = ""
	
    }
	
    stages {
						
		stage('Clone sources') {
		    steps {
			    
			// Clone from git
			git branch: 'master',
				credentialsId: "${SRC_ID}",
				url: "${SRC_URL}"
		    }
		}
	    
		stage ('Checkout') {
			steps { 
				script {
					
					def files = findFiles glob: "${file_cond}"
					
					//Check
					files.each { item ->
						if (item.name.startsWith(file_name_requirements)) {
							file_name = item.name;
							echo 'Checkout sucess'
						}
					}
					
					//Abort if no files founded
					if (file_name == "") {
							currentBuild.result = 'ABORTED'
							error('Checkout failed')
					}
					
				}
			}
		}
			
		stage('Transition') {
		    steps {
			  script {
			    	bat("xcopy ${WORKSPACE} ${SERVER_PATH}")
			    }
		    }
		}
	    
		stage('Deploy Lambda') {
		    steps {
			echo "..."
		    }
		}
	    
		stage('Test') {
		    steps {
			echo "..."
		    }
		}
    }
}
