/*globals describe, it, expect, element, browser*/
describe('DCI homepage', function () {
  it('should display a login page', function () {
      browser.get('/');
      expect(browser.getTitle()).toEqual('Distributed CI');
    });
});
