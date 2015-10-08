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

.controller('JobCtrl', ['$scope', 'job', function($scope, job) {
  $scope.job = job;
}])
