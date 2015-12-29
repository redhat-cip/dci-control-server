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
      var status = $injector.get('status');
      var $state = $injector.get('$state');

      var job = scope.job;
      var start = moment(job.created_at);
      job.time_running = moment(job.updated_at).to(job.created_at, true);
      job.updated_at = moment(job.updated_at).from(moment.moment());

      job.glyphicon = status[job.status]['glyphicon'];
      job.statusClass = 'bs-callout-' + status[job.status]['color'];


      scope.recheck = function() {
        api.recheckJob(job.id).then(function(job) {
          $state.go('job', {id: job.id});
        });
      }
    },
    templateUrl: '/partials/dci-job.html'
  };
}]);
