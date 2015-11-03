require('./app.js')

.controller('LoginCtrl', [
  '$scope', '$state', 'next', 'auth',
  function($scope, $state, next, auth) {
    $scope.authenticate = function(credentials) {
      auth.login(credentials.username, credentials.password);
      $state.go(next.state, next.args);
    }
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
    var end = moment(new Date(job.jobstate.created_at));
    var start = moment(new Date(job.jobstates[0].created_at));

    job.jobstate.created_at = moment(new Date(job.jobstate.created_at)).fromNow()
    job.timeRunning = end.to(start, true);

    var status = $scope.status = job.jobstate.status;

    end = moment(job.jobstates[job.jobstates.length]);
    start = moment(job.jobstates[0]);

    var glyphiconStatus = {
      'failure': 'glyphicon-remove',
      'success': 'glyphicon-ok',
      'new': 'glyphicon-record',
      'initializing': 'glyphicon-record',
      'killed': 'glyphicon-minus',
      'unfinished': 'glyphicon-minus'
    };

    $scope.glyphicon = function () {
      return glyphiconStatus[status];
    }
  }
]);
