require('./app.js')

.factory('api', ['$resource', '$q', function($resource, $q) {
  var Jobs = $resource('/api/jobs/:id');
  var JobStates = $resource('/api/jobstates');
  var CIs = $resource('/api/remotecis');
  var TestVersions = $resource('/api/testversions/:id');
  var Products = $resource('/api/products/:id');

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

  function getJob(id) {
    var job;

    return $q.all([
      Jobs.get({
        'id': id, 'embedded': {'remoteci': 1, 'testversion': 1}
      }).$promise,
      JobStates.get({
        'where': {'job_id': id},
        'sort': 'created_at',
        'embedded': {'files_collection': 1}
      }).$promise
    ]).then(function(data) {
      job = data.shift();
      job.jobstate = data.shift()._items.pop();
      return TestVersions.get({
        id: job.testversion.id,
        'embedded': {'version': 1, 'test': 1}
      }).$promise;
    }).then(function(testversion) {
      job.version = testversion.version.name;
      job.test = testversion.test.name;
      return Products.get({
        id: testversion.version.product_id
      });
    }).then(function(product) {
      job.product = product.name;
      return job
    });
  }

  return {
    getJobs: getJobs,
    getJob: getJob,
    getCIs: getCIs
  }
}]);


