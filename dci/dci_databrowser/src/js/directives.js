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
.directive('dciJob', ['$injector', function($injector) {
  return {
    link: function(scope) {
      var _ = $injector.get('_');
      var api = $injector.get('api');
      var moment = $injector.get('moment');
      var glyphicon = $injector.get('glyphiconStatus');
      var $state = $injector.get('$state');

      var job = scope.job;

      api.getJobStates(job.id).then(function(jobstates) {
        if (!jobstates.length)  return;
        var jobstate = _.last(jobstates);

        var end = moment(jobstate.created_at);
        var start = moment(_.first(jobstates).created_at);
        job.status = jobstate.status;
        job.createdAt = start.fromNow()
        job.timeRunning = end.to(start, true);
        job.glyphicon = glyphicon(job.status);
      });

      scope.recheck = function() {
        api.recheckJob(job.id).then(function(job) {
          $state.go('job', {id: job.id});
        });
      }
    },
    templateUrl: '/partials/dci-job.html'
  };
}]);
