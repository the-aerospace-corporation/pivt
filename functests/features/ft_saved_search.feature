Feature: FT saved search reports correctly
	FT scenarios saved search combines FT runs, pipeline runs, and scenarios. Check if this is done correctly.

	Scenario: Nominal is all and tag is all
		When the search is run with nominal=all and tag=all
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 283    | 2636     | false   | 5          | 3           | 2           | 2          | 1           |
			| ci1 | 284    | 2637     | true    | 5          | 1           | 4           | 2          | 0           |
			| ci1 | 285    | 2638     | false   | 5          | 5           | 0           | 2          | 2           |

	Scenario: Nominal is yes and tag is all
		When the search is run with nominal=yes and tag=all
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 284    | 2637     | true    | 5          | 1           | 4           | 2          | 0           |

	Scenario: Nominal is no and tag is all
		When the search is run with nominal=no and tag=all
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 283    | 2636     | false   | 5          | 3           | 2           | 2          | 1           |
			| ci1 | 285    | 2638     | false   | 5          | 5           | 0           | 2          | 2           |

	Scenario: Nominal is all and tag is core
		When the search is run with nominal=all and tag=core
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 283    | 2636     | false   | 2          | 1           | 1           | 2          | 1           |
			| ci1 | 284    | 2637     | true    | 2          | 0           | 2           | 2          | 0           |
			| ci1 | 285    | 2638     | false   | 2          | 2           | 0           | 2          | 2           |

	Scenario: Nominal is all and tag is notcore
		When the search is run with nominal=all and tag=notcore
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 283    | 2636     | false   | 3          | 2           | 1           | 2          | 1           |
			| ci1 | 284    | 2637     | true    | 3          | 1           | 2           | 2          | 0           |
			| ci1 | 285    | 2638     | false   | 3          | 3           | 0           | 2          | 2           |

	Scenario: Nominal is yes and tag is core
		When the search is run with nominal=yes and tag=core
		Then the results should be
			| ci  | number | p_number | nominal | scen_count | scen_passed | scen_failed | core_tests | core_passed |
			| ci1 | 284    | 2637     | true    | 2          | 0           | 2           | 2          | 0           |
