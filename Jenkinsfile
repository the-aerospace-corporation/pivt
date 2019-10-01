// Copyright 2019 The Aerospace Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

node {
    stage('Prep') {
        checkout scm

        release_suffix = env.BRANCH_NAME.startsWith("release/") ? "RC-$BUILD_NUMBER" : env.BRANCH_NAME == "develop" ? "SNAPSHOT" : ""

        sh 'find $WORKSPACE -name "*.sh" -exec chmod +x {} +'
    }
    stage('UnitTest'){
        sh 'sh $WORKSPACE/docker/unit-test.sh'
        junit '**/docker/ut_data/ut_report.xml'
        cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: '**/docker/ut_data/coverage.xml', conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
        warnings canComputeNew: false, canResolveRelativePaths: true, categoriesPattern: '', defaultEncoding: '', excludePattern: '', healthy: '', includePattern: '', messagesPattern: '', parserConfigurations: [[parserName: 'PyLint', pattern: '**/docker/ut_data/pylint.out']], unHealthy: ''
    }
    stage('Build') {
        // get lookups from Artifactory
        withCredentials([string(credentialsId: 'artifactory-api-key', variable: 'ARTIFACTORY_API_KEY')]) {
            sh '$WORKSPACE/pull_lookups.sh $ARTIFACTORY_API_KEY'
        }

        // run release.sh; source it so we get the variables from the script in this shell; echo the release variable from the script
        // use tokenize() function to split output by whitespace and get the last line (from the echo)
        release = sh(returnStdout: true, script: "source $WORKSPACE/release.sh ${release_suffix}; echo \$release").tokenize()[-1]
        release_name = release.split('/')[-1]

        archiveArtifacts(artifacts: "${release_name}*", onlyIfSuccessful: true)

        sh 'rels="$WORKSPACE/docker/aero-pivt-*"; if [ ! -z "$(ls $rels)" ]; then rm $rels; fi'
        sh "mv ${release} $WORKSPACE/docker"

        release = "$WORKSPACE/docker/${release_name}"
    }
    stage('FuncTest') {
        withCredentials([file(credentialsId: 'splunk-license', variable: 'splunk_license')]) {
            sh 'cp $splunk_license $WORKSPACE/docker/Splunk.License.lic'
        }

        sh 'sh -x $WORKSPACE/docker/func-test.sh --no-release'
        cucumber buildStatus: 'UNSTABLE',
                 fileIncludePattern: '**/docker/ft_report.json',
                 trendsLimit: 50
    }
    if (env.JOB_NAME.startsWith("pivt/")) {
        stage('Deploy') {
            if (env.BRANCH_NAME == "develop") {
                sh "sh -x $WORKSPACE/deploy.sh -y pivt-dev-vm ${release}"
            }
            else if (env.BRANCH_NAME == "master") {
                sh "sh -x $WORKSPACE/deploy.sh -y pivt-vm ${release}"
            }
        }
    }
}
