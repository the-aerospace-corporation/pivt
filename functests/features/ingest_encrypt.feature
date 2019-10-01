Feature: Different files with same first 256 bytes are ingested into Splunk
	Two files may contain the same 256 bytes and Splunk's default ingestion will not take the second file even if the second one is different after the same 256 bytes.

	Scenario Outline: Two files first 256 bytes are the same in the Jenkins folder with crcSalt on
		Given <Input> exist in the "jenkins" folder
		And <Input> have the same 256 bytes in the "jenkins" folder
		Then <Expected> should be in "pivt_jenkins" splunk index and "jenkins" folder

		Examples: Input Variables
			| Input									 | Expected                               |
			| ["ci2_build1.json", "ci2_build2.json"] | ["ci2_build1.json", "ci2_build2.json"] |

	Scenario Outline: Two files first 256 bytes are the same in the Vic folder with crcSalt off
		Given <Input> exist in the "vic" folder
		And <Input> have the same 256 bytes in the "vic" folder
		Then <Expected> should be in "pivt_vic" splunk index and "vic" folder

		Examples: Input Variables
			| Input					     | Expected      |
			| ["vic1.json", "vic2.json"] | ["vic1.json"] |