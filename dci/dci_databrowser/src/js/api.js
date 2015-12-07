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
.constant('apiURLS', {
  JOBS: '/api/v1/jobs/',
  REMOTECIS: '/api/v1/remotecis/',
  JOBSTATES: '/api/v1/jobstates/',
  FILES: '/api/v1/files/'
})
.factory('api', ['_', '$q', '$http', 'apiURLS', function(_, $q, $http, urls) {

  function getJobs(page) {
    var offset = 20 * (page - 1);
    var config = {
      'params': {
        'limit': 20, 'offset': offset,
        'embed': 'remoteci,jobdefinition,jobdefinition.test'
      }
    };
    return $http.get(urls.JOBS, config).then(_.property('data'));
  }

  function getJobStates(job) {
    var url = urls.JOBS + job + '/jobstates';
    return $http.get(url).then(_.property('data.jobstates'));
  }

  function searchJobs(remotecis, statuses) {

    function retrieveJSs(status) {
      var conf = {'params': {'where': 'status:' + status}};
      return $http.get(urls.JOBSTATES, conf);
    }

    function retrieveRCIs(remoteci) {
      var conf = {'params': {'where': 'name:' + remoteci}};
      return $http.get(urls.REMOTECIS, conf);
    }

    function retrieveJsRCI(remoteciResps) {
      return _(remoteciResps)
      .map(_.property('data.remotecis'))
      .flatten()
      .map(_.property('id'))
      .map(function(remoteci){
        var conf = {'params': {'where': 'remoteci_id:' + remoteci}};
        return $http.get(urls.JOBS, conf);
      })
      .thru($q.all)
      .value()
      .then(_.partialRight(_.map, _.property('data.jobs')))
      .then(_.flatten)
      .then(_.partialRight(_.map, _.property('id')));
    }

    function retrieveJsS(jobstateResps) {
      return _(jobstateResps)
      .map(_.property('data.jobstates'))
      .flatten()
      .map(_.property('job_id'))
      .uniq()
      .map(function(job) {
        var conf = {'params': {
          'where': 'job_id:' + job, 'sort': '-created_at', 'limit': 1
        }};
        return $http.get(urls.JOBSTATES, conf);
      })
      .thru($q.all)
      .value()
      .then(_.partialRight(_.map, _.property('data.jobstates')))
      .then(_.flatten)
      .then(_.partialRight(_.filter, function(jobstate) {
        return _.include(statuses, jobstate.status);
      }))
      .then(_.partialRight(_.map, _.property('job_id')));
    }

    return $q.all([
      _(remotecis).map(retrieveRCIs).thru($q.all).value().then(retrieveJsRCI),
      _(statuses).map(retrieveJSs).thru($q.all).value().then(retrieveJsS)
    ])
    .then(function(data) {
      var remotecisJobs = data[0];
      var statusesJobs = data[1];
      if (statusesJobs.length && remotecisJobs.length) {
        return _.intersection(statusesJobs, remotecisJobs);
      } else {
        return statusesJobs.concat(remotecisJobs);
      }
    })
    .then(function(jobs) {
      return $q.all(_.map(jobs, function(job) {
        var config = {'params': {
          'embed': 'remoteci,jobdefinition,jobdefinition.test',
        }};
        return $http.get(urls.JOBS + job, config);
      }));
    })
    .then(_.partialRight(_.map, _.property('data.job')))
    .then(function(jobs) {
      return {'jobs': jobs};
    });
  }

  function getJob(job) {
    var retrieveFiles = function(data) {
      var job = _.assign(_.first(data).data.job,
                         {'jobstates': _.last(data).data.jobstates});

      return _.map(job.jobstates, function(js) {
        var conf = {'params': {'where': 'jobstate_id:' + js.id}};
        return $http.get(urls.FILES, conf);
      }).concat([job]);
    }

    var parseFiles = function(data) {
      _(data)
      .initial()
      .map(_.property('data.files'))
      .zip(_.last(data).jobstates)
      .map(function(elt) {
        return _.assign(_.last(elt), {'files': _.first(elt)})
      })
      .value();

      var job = _.last(data);
      job.jobstate = _.last(job.jobstates);
      return job;
    }
    var conf = {'params': {'embed': 'remoteci,jobdefinition'}};

    return $q.all([
      $http.get(urls.JOBS + job, conf),
      $http.get(urls.JOBS + job + '/jobstates')
    ])
    .then(retrieveFiles)
    .then($q.all)
    .then(parseFiles);
  }

  function getRemoteCIS() {
    var extractRemoteCIS = _.partialRight(_.get, 'data.remotecis');
    return $http.get(urls.REMOTECIS).then(extractRemoteCIS);
  }

  function recheckJob(jobID) {
    return $http.post(urls.JOBS + jobID + '/recheck')
    .then(_.property('data.job'));
  }

  return {
    getJobs: getJobs,
    getJob: getJob,
    getJobStates: getJobStates,
    getRemoteCIS: getRemoteCIS,
    recheckJob: recheckJob,
    searchJobs: searchJobs
  }
}]);
