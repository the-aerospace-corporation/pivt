# Copyright 2019 The Aerospace Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

###################################################################
# The purpose of this script is to automate CQ DRs csv file
#
# Set/export/mask 'cq_user_id' and 'cq_user_pass' as env variables
#

use CQPerlExt;
use warnings;
use strict;

my %CQ_LOGIN = (
   #'username' => 'YOUR_USER_ID_IN_ClearQuest',
   #'password' => 'YOUR_SECRET_PASSWORD_IN_ClearQuest!',
	'username' => $ENV{'cq_user_id'},
	'password' => $ENV{'cq_user_pass'},
	'repo'     => 'GPSOCX'
);

my $session = CQSession::Build();
$session->UserLogon($CQ_LOGIN{'username'}, $CQ_LOGIN{'password'}, 'USDL', $CQ_LOGIN{'repo'});
my $workspace = $session->GetWorkSpace();

my $querydef = $workspace->GetQueryDef("Public Queries/SandBox/PIVT/pivt-drs");
#my $querydef = $workspace->GetQueryDef("Public Queries/SandBox/PIVT/pivt-drs-all-iterations-mcse-2018");
my $resultset = $session->BuildResultSet($querydef);
$resultset->EnableRecordCount();
$resultset->Execute();

my $recordCount = $resultset->GetRecordCount();
my $cols = $resultset->GetNumberOfColumns() - 1;
my $var = 0; my $i = 0;

if ( $recordCount == 0 ) {
	print "\n\n- No files in query\n\n";
}

## If you want, you can overwrite the target final CSV file but that's not good if things break during the operation.
## Create a temporary CSV file, later on, you can move this file to the final CSV location file.
open (FH, ">queryClearQuest_generated_file.csv") or die "$!";

for ( my $x=0; $x < $recordCount; $x++ ) {
	## Print Field/Header Labels of a givn query - ONLY ONCE i.e. TOP ROW in CSV file - will be field/header names
	if ( $x == 0 ) {
		for ( $i = 2; $i < $resultset->GetNumberOfColumns() + 1; $i++) {
			print FH $resultset->GetColumnLabel($i);
			if ( $i <= $cols ) { print FH ","; }
		}
		print FH "\n";
	}

	## Print Field values for each row ($x) and iterate over each column ($i)
	$resultset->MoveNext();
	for ( $i = 2; $i < $resultset->GetNumberOfColumns() + 1; $i++) {
		$var = $resultset->GetColumnValue($i);
		## Remove any \r\n within CSV field's value.
		$var =~ s/\r//g;
		$var =~ s/\n/, /g;
		## Wrap/pad a double quote within a field's value, with another double-quote character
		$var =~ s/"/""/g;
		print FH "\"$var\"";
		if ( $i <= $cols ) { print FH ","; }
	}
	print FH "\n";
}
close(FH);

print "\nTotal # of records processed: $recordCount\n";
print "Total # of columns in query : " . $resultset->GetNumberOfColumns() . "\n\n";

## Move file logic can go here or you can do that via Jenkins. For doing within Perl, refer the following URL.
## https://alvinalexander.com/blog/post/perl/how-move-rename-file-perl

CQSession::Unbuild($session);
