require('./app.js')

.factory('api', ['$resource', function($resource) {
  var Jobs = $resource('/api/jobs');

  function getJobs(page) {
    return Jobs.get({
      page: page,
      extra_data: 1,
      sort: '-created_at'
    }).$promise
  }

  return {
    getJobs: getJobs
  }
}]);


