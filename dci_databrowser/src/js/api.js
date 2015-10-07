require('./app.js')

.factory('api', ['$resource', function($resource) {
  var Jobs = $resource('/api/jobs');
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
      extra_data: 1,
      sort: '-created_at'
    }).$promise;
  }

  return {
    getJobs: getJobs,
    getCIs: getCIs
  }
}]);


