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
use warnings;
use strict;
use CQPerlExt;

# Pad a number n with a 0 if n < 10
#
# arg_0: A number n to be used in a Date
# return: A string that is '0n' if n < 10 or n if n >= 10
sub padZero
{
    if ($_[0] < 10) {
        return "0" . $_[0];
    }
    return $_[0];
}

# Gets the header information for a result set
#
# arg_0: The result set
# return: An array reference of header values
sub getHeaders
{
    my $resultSet = $_[0];
    my $cols = $resultSet->GetNumberOfColumns() + 1;
    my $headers = [];
    for (my $i = 2; $i < $cols; $i++) {
        push(@$headers, $resultSet->GetColumnLabel($i));
    }
    return $headers;
}

# UNUSED; Add entries from a CQ result set to an in memory representation of the CQ database
#
# arg_0: Reference to the result set
# arg_1: Reference to the in memory hash
# arg_2: Reference to an array of keys (headers)
# return: N/A
sub addTableEntries
{
    my $resultSet = $_[0];
    my $cqtable = $_[1];
    my $keys = $_[2];

    my $recordCount = $resultSet->GetRecordCount();
    my $cols = $resultSet->GetNumberOfColumns() + 1;
    my $idcol = 4; # This is the column that holds the id
    my $datecol = 2; # This is the column that holds the date
    my $curid = undef;

    for (my $r = 1; $r < $recordCount; $r++) {
        $resultSet->MoveNext();
        $curid = $resultSet->GetColumnValue($idcol);
        print "curid: $curid\n";
        # Overwrite an existing entry only if the date is after the current date
        if ($$cqtable{$curid}) {
            if ($$cqtable{$curid}->[0] lt $resultSet->GetColumnValue($datecol)) {
                for (my $i = 2; $i < $cols; $i++) {
                    $$cqtable{$curid}->[$i - 2] = $resultSet->GetColumnValue($i);
                }
            }
        } else {
            $$cqtable{$curid} = [];
            for (my $i = 2; $i < $cols; $i++) {
                push(@{$$cqtable{$curid}}, $resultSet->GetColumnValue($i));
            }
        }
    }
}

sub writeHeader
{
    my $fh = $_[0];
    my $headers = $_[1];

    my $cols = scalar @{$headers};

    for (my $i = 0; $i < $cols; $i++) {
        print $fh $headers->[$i];
        if ($i < $cols - 1) {
            print $fh ",";
        }
    }

    print $fh "\n"
}

sub writeResults
{
    my $fh = $_[0];
    my $resultSet = $_[1];

    my $recordCount = $resultSet->GetRecordCount();
    my $cols = $resultSet->GetNumberOfColumns() + 1;

    for (my $x = 0; $x < $recordCount; $x++) {
        $resultSet->MoveNext();

        for (my $i = 2; $i < $cols; $i++) {
            my $val = $resultSet->GetColumnValue($i);
            ## Remove any \r\n within CSV field's value.
            $val =~ s/\r//g;
            $val =~ s/\n/, /g;
            ## Wrap/pad a double quote within a field's value, with another double-quote character
            $val =~ s/"/""/g;
            print $fh "\"$val\"";
            if ($i < $cols - 1) {
                print $fh ",";
            }
        }
        print $fh "\n";
    }

    return $recordCount;
}

# UNUSED; Writes a result set to a csv file
#
# arg_0: The in memory representation of the CQ query
# arg_1: The file handler of the file to write to
# arg_2: The headers for the CQ query
# return: N/A
sub writeQuery
{
    my $cqtable = $_[0];
    my $fh = $_[1];
    my $headers = $_[2];
    my $cols = scalar @{$headers};

    # Write Header information
    for (my $i = 0; $i < $cols; $i++) {
        print $fh $headers->[$i];
        if ($i < $cols - 1) {
            print $fh ",";
        }
    }

    # Write Records
    foreach my $id (keys %{$cqtable}) {
        for (my $i = 0; $i < $cols; $i++) {
            my $row = $$cqtable{$id}->[$i];
            $row =~ s/\r//g;
            $row =~ s/\n/, /g;
            $row =~ s/"/""/g;
            print $fh "\"$row\"";
            if ($i < $cols - 1) {
                print $fh ",";
            }
        }
        print $fh "\n";
    }
}

# Get a formatted date from a POSIX epoch time
#
# arg_0: POSIX epoch time
# return: Date string formatted as %m/%d/%Y %H:%M:%S
sub dateFromEpoch
{
    my $epoch = $_[0];
    my ($sec, $min, $hour, $day, $month, $year) = (gmtime($epoch))[0,1,2,3,4,5];
    $sec = padZero($sec);
    $min = padZero($min);
    $month = $month + 1;
    $year = $year + 1900;
    return $month . "/" . $day . "/" . $year . " " . $hour . ":" . $min . ":" . $sec;
}

# Get a POSIX epoch time value within an interval
#
# arg_0: Lower time bound in POSIX epoch time
# arg_1: Upper bound in POSIX epoch time
# arg_2: Time increment in POSIX epoch time
# return: minimum of arg_0 + arg_1 and arg_2
sub nextTime
{
    my $nexttime = $_[0] + $_[2];
    my $endtime = $_[1];
    if ($nexttime > $endtime) {
        return $endtime;
    }
    return $nexttime;
}

# Import credentials and CQ repository information
my %CQ_LOGIN = (
   #'username' => 'YOUR_USER_ID_IN_ClearQuest',
   #'password' => 'YOUR_SECRET_PASSWORD_IN_ClearQuest!',
    'username' => $ENV{'cq_user_id'},
    'password' => $ENV{'cq_user_pass'},
    'repo'     => 'GPSOCX'
);

# Attempt to load the last pull date in POSIX time format
my $lpfile = $ENV{'PIVT_CQLP'};
my $encoding = ':encoding(UTF-8)';
my $lastpulltime = 1563148800; # Default last pull time (July 15, 2019 12 AM GMT)
if (open(my $fh, '<' . $encoding, $lpfile)) {
    $lastpulltime = <$fh>;
    chomp $lastpulltime;
    $lastpulltime = int($lastpulltime);
    close $fh;
}

# Initialize new pull time
my $newpulltime = time;

# Connect to CQ database
print "Connecting to CQ\n";
my $session = CQSession::Build();
$session->UserLogon($CQ_LOGIN{'username'}, $CQ_LOGIN{'password'}, 'USDL', $CQ_LOGIN{'repo'});
my $workspace = $session->GetWorkSpace();

my $date = dateFromEpoch($lastpulltime);
print "Pulling added/modifed CQ DRs since $date GMT\n";

# Write the added/modified records in 1 day chunks
my $amquerypath = "amQueryClearQuest_generated_file.csv"; # file path for added/modified CQ records
if(open(my $fh, '>' . $encoding, $amquerypath)) {
    # Initialize initial time values and flags
    my $curtime = $lastpulltime;
    my $curtimestr = dateFromEpoch($curtime);
    my $endtime = $newpulltime;
    my $stepsize =  86400; # 24 hours

    # Initialize CQ session
    print "Loading AM query\n";
    my $amquery = $workspace->GetQueryDef('Public Queries/Sandbox/PIVT/pivt-drs-history');
    my $amrset = $session->BuildResultSet($amquery);

    # Set the type of operator to BETWEEN for the dynamic filter in the CQ query
    # The magic number '1' below refers to the '1'st dynamic filter in the query
    # The CQPerlExt package provides an enum of possible operators for dynamic filters
    # Refer to the Rational ClearQuest API Reference for more information
    $amrset->SetParamComparisonOperator(1, $CQPerlExt::CQ_COMP_OP_BETWEEN);

    my $records = 0;

    print "Querying\n";
    while ($curtime < $endtime) {
        my $nexttime = nextTime($curtime, $endtime, $stepsize);
        my $nexttimestr = dateFromEpoch($nexttime);

        # Insert the parameter values for the dynamic filter for CQ query
        # The magic number '1' below refers to the '1'st dynamic filter in the query
        # Each operator has different parameter requirements
        # Refer to the Rational ClearQuest API Reference for more information
        $amrset->ClearParamValues(1);
        $amrset->AddParamValue(1, $curtimestr);
        $amrset->AddParamValue(1, $nexttimestr);

        # Make request to CQ database
        $amrset->EnableRecordCount();
        $amrset->Execute();

        if ($curtime == $lastpulltime) {
            my $headers = getHeaders($amrset);
            writeHeader($fh, $headers);
        }

        $records += writeResults($fh, $amrset);

        # Update step
        $curtime = $nexttime;
        $curtimestr = $nexttimestr;
    }

    close($fh);

    my $duration = time - $newpulltime;

    print "Pulled $records records in $duration seconds\n"
} else {
    die "\nUnable to open file: $amquerypath\n";
}

print "Pulling list of all DR IDs\n";

print "Loading RM query\n";

# Get all record ids for determining removed records
my $rmquery = $workspace->GetQueryDef('Public Queries/Sandbox/PIVT/pivt-drs-ids');
my $rmrset = $session->BuildResultSet($rmquery);

print "Querying\n";

$rmrset->EnableRecordCount();
$rmrset->Execute();

# Write data to files for further processing
my $rmQueryPath = "rmQueryClearQuest_generated_file.csv";

if(open(my $fh, '>' . $encoding, $rmQueryPath)) {
    my $headers = getHeaders($rmrset);
    writeHeader($fh, $headers);

    my $rmRecordCount = 0;
    $rmRecordCount += writeResults($fh, $rmrset);
    print "Total # of records: $rmRecordCount\n\n";

    close($fh);
} else {
    die "\nUnable to open file: $rmQueryPath\n";
}

# Clean up session and write new pull time
CQSession::Unbuild($session);

print "Writing new pull time to file\n";
if (open(my $fh, '>' . $encoding, $lpfile)) {
    print $fh $newpulltime;
    close $fh;
}
else {
    die "\nUnable to create file: $lpfile\n";
}

print "Done\n";
