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

var conf = require('conf');

require('app')

.constant('apiURLS', {
  JOBS: conf.apiURL + '/api/v1/jobs/',
  REMOTECIS: conf.apiURL + '/api/v1/remotecis/',
  JOBSTATES: conf.apiURL + '/api/v1/jobstates/',
  FILES: conf.apiURL + '/api/v1/files/',
  USERS: conf.apiURL + '/api/v1/users/',
  TEAMS: conf.apiURL + '/api/v1/teams/'
})
.factory('api', ['_', '$q', '$http', 'apiURLS', function(_, $q, $http, urls) {
  var api = {};

  api.getJobs = function(page) {
    var offset = 20 * (page - 1);
    var config = {'params': {
        'limit': 20, 'offset': offset, 'sort': '-updated_at',
        'embed': 'remoteci,jobdefinition,jobdefinition.test'
    }};
    return $http.get(urls.JOBS, config).then(_.property('data'));
  }

  api.getJobStates = function(job) {
    var url = urls.JOBS + job + '/jobstates';
    return $http.get(url).then(_.property('data.jobstates'));
  }

  api.searchJobs = function(remotecis, statuses) {

    function retrieveRCIs(remoteci) {
      var conf = {'params': {'where': 'name:' + remoteci}};
      return $http.get(urls.REMOTECIS, conf);
    }

    function retrieveJobs(status) {
      var conf = {'params': {
        'where': 'status:' + status,
        'embed': 'remoteci,jobdefinition,jobdefinition.test'
      }};
      return $http.get(urls.JOBS, conf);
    }

    function retrieveJsRCI(remoteciResps) {
      return _(remoteciResps)
      .map(_.property('data.remotecis'))
      .flatten()
      .map(_.property('id'))
      .map(function(remoteci){
        var conf = {'params': {
          'embed': 'remoteci,jobdefinition,jobdefinition.test',
          'where': 'remoteci_id:' + remoteci,
        }};
        return $http.get(urls.JOBS, conf);
      })
      .thru($q.all)
      .value();
    }
    return $q.all([
      _(remotecis).map(retrieveRCIs).thru($q.all).value().then(retrieveJsRCI),
      _(statuses).map(retrieveJobs).thru($q.all).value()
    ])
    .then(function(data) {
      var getJobs= _().map(_.property('data.jobs')).flatten();
      var RCISJobs = getJobs.plant(_.first(data)).value();
      var SSJobs = getJobs.plant(_.last(data)).value();

      if (SSJobs.length && RCISJobs.length) {
        var RCISJobsIds = _.pluck(RCISJobs, 'id');
        return _.filter(SSJobs, function(job) {
          return _.contains(RCISJobsIds, job.id);
        });
      } else {
        return SSJobs.concat(RCISJobs);
      }
    })
    .then(function(jobs) {
      return {'jobs': jobs};
    });
  }

  api.getJob = function(job) {
    var retrieveFiles = function(data) {
      return _.assign(
        _.first(data).data.job,
        {'jobstates': _.last(data).data.jobstates}
      );
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

      return _.last(data);
    }
    var conf = {'params': {'embed': 'remoteci,jobdefinition'}};
    var JSconf = {'params': {'sort': '-created_at'}};

    return $q.all([
      $http.get(urls.JOBS + job, conf),
      $http.get(urls.JOBS + job + '/jobstates', JSconf)
    ])
    .then(retrieveFiles)
  }

  api.getFiles = function(jobstateID) {
    var conf = {'params': {'where': 'jobstate_id:' + jobstateID}};
    return $http.get(urls.FILES, conf)
    .then(_.property('data.files'));
  }

  api.getRemoteCIS = function() {
    var extractRemoteCIS = _.partialRight(_.get, 'data.remotecis');
    return $http.get(urls.REMOTECIS).then(extractRemoteCIS);
  }

  api.recheckJob = function(jobID) {
    return $http.post(urls.JOBS + jobID + '/recheck')
    .then(_.property('data.job'));
  }

  api.getUser = function(name) {
    var conf = {'params': {'embed': 'team'}};
    return $http.get(urls.USERS + name, conf).then(_.property('data.user'));
  }

  api.getTeams = function() {
    return $http.get(urls.TEAMS).then(_.property('data.teams'));
  }

  api.postTeam = function(team) {
    return $http.post(urls.TEAMS, team).then(_.property('data.team'));
  }

  api.postUser = function(user) {
    return $http.post(urls.USERS, user).then(_.property('data.user'));
  }

  return api;
}]);
