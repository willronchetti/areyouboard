//RESULTS PAGE

$('.results-button').click(function() {
  var offset = $('header').height();
  // if($(window).width() < 550) {
  //   $('#nav-links').slideUp(200);
  //   $('#watermark').slideDown(200);
  //   offset = 60;
  // }

  $('#results-grid').slideUp();
  $('#results-grid2').slideUp();
  // $('#results-grid').css('display', 'none');
    //Talk to harrison about making this smoother via scrolling
  $('#' + $(this).data("id")).slideDown();
  $('html,body').animate({scrollTop:$('#' + $(this).data("id")).offset().top - offset}, 'slow');
});

$('.return').click(function() {
  $(this).parent().slideUp();
  $('#results-grid').slideDown();
  console.log("hi");
  $('#results-grid').css('display', 'block');
  console.log("hi");
});
