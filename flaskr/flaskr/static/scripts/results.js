//RESULTS PAGE
console.log("results js loaded");

$('.results-button').click(function() {
  // if($(window).width() < 550) {
  //   $('#nav-links').slideUp(200);
  //   $('#watermark').slideDown(200);
  //   offset = 60;
  // }
  console.log("hi");

  $('#results-grid').slideUp("slow", "swing");
  $('#results-grid2').slideUp("slow", "swing");
  // $('#results-grid').css('display', 'none');
  $('#' + $(this).data("id")).slideDown();
  // $('html,body').scrollTo("#state1");
  // $('html,body').scrollTo("#state2");

  $('#footer').css('height', '20px');

  // $('html,body').animate({scrollTop:$('#' + $(this).data("id")).offset().top - 50}, 'slow');
});

$('.return-btn').click(function() {
  $('.return').parent().slideUp();
  $('#results-grid').slideDown();
  $('#results-grid2').slideDown();
  $('#results-grid').css('display', 'block');
  $('#results-grid2').css('display', 'block');

  $('#footer').css('height', '50px');
});
