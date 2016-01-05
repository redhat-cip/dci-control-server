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
.controller('LoginCtrl', [
  '$scope', '$state', 'auth', function($scope, $state, auth) {
    $scope.authenticate = function(credentials) {
      auth.login(credentials.username, credentials.password).then(function(){
        $state.go('index');
      });
    }
    $scope.unauthorized = auth.isUnauthorized();
  }
])

.controller('ListJobsCtrl', [
  '$injector', '$scope', 'jobs', 'remotecis', 'page',
  function($injector, $scope, jobs, remotecis, page) {
    var _ = $injector.get('_');
    var $state = $injector.get('$state');
    var statuses = ['failure', 'success', 'running', 'new',
                    'pre-run', 'post-run'];
    $scope.jobs = jobs.jobs;
    $scope.remotecis = {};
    $scope.status = {};
    _.each(statuses, function(status) {
      this[status] = _.contains($state.params.status, status);
    }, $scope.status);

    _.each(remotecis, function(remoteci) {
      var remoteci = remoteci.name;
      this[remoteci] = _.contains($state.params.remoteci, remoteci);
    }, $scope.remotecis);


    $scope.search = function () {
      var params = {
        'status': _($scope.status).pick(_.identity).keys().join(','),
        'remoteci': _($scope.remotecis).pick(_.identity).keys().join(',')
      }
      $state.go('jobs', params);
    }

    $scope.isFiltering = !!(
      $state.params.status.length || $state.params.remoteci.length
    );

    if (!$scope.isFiltering) {
      $scope.pagination = {
        total: jobs._meta.count, page: page,
        pageChanged: function() {
          $state.go('jobs', $scope.pagination);
        }
      };
    }
  }
])
.controller('JobCtrl', [
  '$scope', 'job', 'api', 'status', 'moment',
  function($scope, job, api, status, moment) {
    $scope.job = job;
    var opened = false;
    job.jobdefinition.created_at = moment.format(job.jobdefinition.created_at);
    job.jobdefinition.updated_at = moment.format(job.jobdefinition.updated_at);

    job.remoteci.created_at = moment.format(job.remoteci.created_at);
    job.remoteci.updated_at = moment.format(job.remoteci.updated_at);

    var test = job.jobdefinition.test;
    test.created_at = moment.format(test.created_at);
    test.updated_at = moment.format(test.updated_at);

    angular.forEach(job.jobstates, function(jobstate) {
      jobstate.statusClass = 'bs-callout-' + status[jobstate.status]['color'];
      api.getFiles(jobstate.id).then(function(files) {
        if (!opened && files.length) {
          opened = jobstate.isOpen = true;
        }
        jobstate.files = files
      });
    });
    api.getComponents(job.jobdefinition.id).then(function(components) {
      $scope.components = components;
    });
  }
])

.controller('AdminCtrl', [
  '$scope', 'teams', 'api', function($scope, teams, api) {
    $scope.teams = teams;
    $scope.team = {};
    $scope.user = {
      admin: false,
      team: teams.length && teams[0].id
    };
    $scope.alerts = [];

    $scope.closeAlert = function(index) {
      $scope.alerts.splice(index, 1);
    };

    $scope.showError = function(form, field) {
      return field.$invalid && (field.$dirty || form.$submitted);
    }

    $scope.submitUser = function() {
      if ($scope.userForm.$invalid) return;
      var user = {
        name: $scope.user.name,
        password: $scope.user.password,
        role: $scope.user.admin ? 'admin' : 'user',
        team_id: $scope.user.team
      }
      api.postUser(user).then(
        function(user) {
          $scope.alerts.push({
            msg: 'Successfully created user "' + user.name + '"',
            type: 'success'
          });
        },
        function(error) {
          $scope.alerts.push({
            msg: 'Error user "' + $scope.user.name + '" already exist',
            type: 'danger'
          })
        }
      );
    }
    $scope.submitTeam = function() {
      if ($scope.teamForm.$invalid) return;
      api.postTeam({name: $scope.team.name}).then(
        function(team) {
          $scope.teams.push(team);
          $scope.alerts.push({
            msg: 'Successfully created team "' + team.name + '"',
            type: 'success'
          });
        },
        function(error) {
          $scope.alerts.push({
            msg: 'Error team "' + $scope.team.name + '" already exist',
            type: 'danger'
          })
        }
      );
    }
  }
]);
