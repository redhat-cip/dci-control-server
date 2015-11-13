// Copyright 2015 Red Hat, Inc.
//
// Licensed under the Apache License, Version 2.0 (the 'License'); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.

'use strict';

require('app')
.factory('api', ['$resource', '$q', function($resource, $q) {
  var Jobs = $resource('/api/jobs/:id?recheck=:recheck&job_id=:jobID');
  var JobStates = $resource('/api/jobstates');
  var JobDefinitions = $resource('/api/jobdefinitions/:id');
  var CIs = $resource('/api/remotecis');

  function getCIs(page) {
    return CIs.get({
      page: page,
      sort: '-created_at'
    }).$promise;
  }

  function getJobs(page) {
    return Jobs.get({
      page: page,
      sort: '-created_at',
      embedded: {
        'jobstates': 1,
        'jobdefinition': 1,
        'remoteci': 1
      },
      projection: {remoteci: 1}
    }).$promise;
  }

  function getJobDefinitions(page) {
    return JobDefinitions.get({
      page: page,
      sort: '-created_at'
    }).$promise;

  }

  function getJobDefinition(id) {
    return JobDefinitions.get({
      'id': id,
      embedded: {'components': 1}
    }).$promise;
  }


  function getJob(id) {
    var job;

    return $q.all([
      Jobs.get({
        'id': id, 'embedded': {'remoteci': 1, 'jobdefinition': 1}
      }).$promise,
      JobStates.get({
        'where': {'job_id': id},
        'sort': 'created_at',
        'embedded': {'files': 1}
      }).$promise
    ]).then(function(data) {
      job = data.shift();
      job.jobstates = data.shift()._items;
      job.jobstate = job.jobstates[job.jobstates.length - 1]
      return job;
    });
  }

  function recheckJob(job) {
    return Jobs.save(
      {jobID: job.id, recheck: 1},
      {remoteci_id: job.remoteci.id, recheck: true}
    ).$promise;
  }


  return {
    getJobs: getJobs,
    getJob: getJob,
    recheckJob: recheckJob,
    getJobDefinitions: getJobDefinitions,
    getJobDefinition: getJobDefinition,
    getCIs: getCIs
  }
}]);


