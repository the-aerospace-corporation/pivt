/*
Copyright 2019 The Aerospace Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

function cleanseSelection(selection, defaultValue) {
	// check if there is more than one entry and one of them is "*"
	if (selection.length > 1 && ~(selection.indexOf("*"))) {
		if (selection.indexOf("*") == 0) {
			// "*" was first, remove it and leave rest
			selection.splice(selection.indexOf("*"), 1);
			return selection;
		} else {
			// "*" was added later, remove rest and leave "*"
			return "*";
		}
	} else if (selection.length < 1) {
		return defaultValue;
	}

	return null;
}

function validateCheckInput(id, mvc) {
	var input = mvc.Components.get(id);

	if (typeof input == "undefined") {
		return;
	}

	console.log("validating " + id);
	console.log("input:");
	console.log(input);

	input.on("change", function() {
		// get the current selection
		selection = input.val();
		defaultValue = input.options.default;

		newSelection = cleanseSelection(selection, defaultValue);

		if (newSelection) {
			input.val(newSelection);
			input.render();
		}
	});
}

function validateCheckInputs(mvc) {
	for (var i = 1; i <= 10; i++) {
		id = "checkboxinput" + i;
		validateCheckInput(id, mvc);

		id = "multiinput" + i;
		validateCheckInput(id, mvc);
	}
}


require([
	"splunkjs/mvc",
	"splunkjs/mvc/simplexml/ready!"
], function(mvc) {
	console.log("validating checkbox and multi input selections");
	validateCheckInputs(mvc);
});
