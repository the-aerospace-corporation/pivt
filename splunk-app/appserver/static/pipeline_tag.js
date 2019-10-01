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

require([
	"splunkjs/mvc",
	"splunkjs/mvc/simplexml/ready!"
], function(mvc) {
    var element_tag_text_box = mvc.Components.get('element_tag_text_box')

    var pipelines_search = mvc.Components.get('elementSearch')

    var service = mvc.createService({ owner: "nobody" });
    var defaultTokenModel = mvc.Components.get("default");

    function do_stuff() {
        // get the current selection
        pipeline_url = defaultTokenModel.get("job_url");
        element_tag = element_tag_text_box.val();

        console.log('selected pipeline run: ' + pipeline_url);
        console.log('element tag: ' + element_tag);

        service.get(
            "storage/collections/data/pipeline_element_kvstore/"
        ).done(function(data) {
            var records = JSON.parse(data)

            var keys = []
            records.forEach(function(item, index, array) {
                keys.push(item['_key'])
            });

            console.log(keys)

            if (pipeline_url && element_tag) {
                var record = {
                    '_key': pipeline_url,
                    'element': element_tag
                };

                if (!keys.includes(pipeline_url)) {
                    console.log('creating record')

                    service.request(
                        "storage/collections/data/pipeline_element_kvstore/",
                        "POST",
                        null,
                        null,
                        JSON.stringify(record),
                        {"Content-Type": "application/json"},
                        null
                    ).done(function() {
                        pipelines_search.startSearch();
                    });
                } else {
                    console.log('updating record')

                    service.request(
                        "storage/collections/data/pipeline_element_kvstore/" + encodeURIComponent(pipeline_url),
                        "POST",
                        null,
                        null,
                        JSON.stringify(record),
                        {"Content-Type": "application/json"},
                        null
                    ).done(function() {
                        pipelines_search.startSearch();
                    });
                }
            } else {
                console.log('deleting record')

                service.del(
                    "storage/collections/data/pipeline_element_kvstore/" + encodeURIComponent(pipeline_url)
                ).done(function() {
                    pipelines_search.startSearch();
                });
            }

            console.log('done')
        });
    }

    $(document).on('click', '#submitButton', function(e) {
        do_stuff();
    });
});