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

require('./app.js')
.controller('LoginCtrl', [
  '$scope', '$state', 'next', 'auth', 'authStates',
  function($scope, $state, next, auth, authStates) {
    $scope.authenticate = function(credentials) {
      auth.login(credentials.username, credentials.password);
      $state.go(next.state, next.args);
    }
    $scope.unauthorized = auth.state == authStates.UNAUTHORIZED;
  }
])

.controller('ListJobsCtrl', [
  '$state', '$scope', 'jobs', 'page', function($state, $scope, jobs, page) {
    $scope.jobs = jobs._items;
    $scope.page = page;

    var total = $scope.total =
      Math.ceil(jobs._meta.total / jobs._meta.max_results);

    var go = function(page) {
      return function () {
        $state.go('jobs', {
          'page': page > total && total || page > 0 && page || 1
        });
      }
    }

    $scope.previous = go(page - 1);
    $scope.next = go(page + 1);
  }
])

.controller('ListJobDefinitionsCtrl', [
  '$state', '$scope', 'jobdefinitions', 'page',
  function($state, $scope, jobdefinitions, page) {
    $scope.jobdefinitions = jobdefinitions._items;
    $scope.page = page;

    var total = $scope.total =
      Math.ceil(jobdefinitions._meta.total / jobdefinitions._meta.max_results);

    var go = function(page) {
      return function () {
        $state.go('jobdefinitions', {
          'page': page > total && total || page > 0 && page || 1
        });
      }
    }

    $scope.previous = go(page - 1);
    $scope.next = go(page + 1);
  }
])
.controller('JobDefinitionCtrl', [
  '$scope', 'jobdefinition', function($scope, jobdefinition) {
    $scope.jobdefinition = jobdefinition;
  }
])
.controller('ListCIsCtrl', [
  '$state', '$scope', 'cis', 'page', function($state, $scope, cis, page) {
    $scope.cis = cis._items;
    $scope.page = page;
    var total = $scope.total =
      Math.ceil(cis._meta.total / cis._meta.max_results);

    var go = function(page) {
      return function () {
        $state.go('remotecis', {
          'page': page > total && total || page > 0 && page || 1
        });
      }
    }

    $scope.previous = go(page - 1);
    $scope.next = go(page + 1);
  }
])

.controller('JobCtrl', [
  '$scope', 'job', 'moment', function($scope, job, moment) {
    $scope.job = job;
    job.jobstate = job.jobstate || {created_at: null};

    var end = moment(job.jobstate.created_at);
    var start = moment(
      job.jobstates.length ? job.jobstates[0].created_at : null
    );

    job.jobstate.created_at = end.fromNow()
    job.timeRunning = end.to(start, true);

    var status = $scope.status = job.jobstate.status;
    var glyphiconStatus = {
      'failure': 'glyphicon-remove',
      'success': 'glyphicon-ok',
      'new': 'glyphicon-record',
      'initializing': 'glyphicon-record',
      'killed': 'glyphicon-minus',
      'unfinished': 'glyphicon-minus'
    };

    $scope.glyphicon = function() {
      return glyphiconStatus[status];
    }

  }
])
.controller('JobRecheckCtrl', [
  '$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.recheck = function(job) {
      api.recheckJob(job).then(function(job) {
        $state.go('job', {'id': job.id});
      });
    }
  }
]);
