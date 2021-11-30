// Holoseat App JS Helper Functions

// Global - e.g. used with the top command bar (Enable, Profiles, Cadence)
function isActive(elementId) {
  return $(elementId).hasClass('active');
}

// Serial Monitor
function toggleSerialMonitorStates(buttonId, textId) {
  if (isActive(buttonId))
    $(textId).text('Off');
  else
    $(textId).text('On');

  $(buttonId).blur();
}

function appendSerialData(data) {
  serialMonitorOutput = $('#serialMonitorOutput');
  serialMonitorOutput.val(serialMonitorOutput.val() + data);
  if (isActive('#autoScrollEnabledButton') && serialMonitorOutput.length)
    serialMonitorOutput.scrollTop(serialMonitorOutput[0].scrollHeight - serialMonitorOutput.height());
}

function clearSerialMonitorOutput() {
  $('#serialMonitorOutput').val('');
  $('#serialMonitorOutput').scrollTop(0);
  $('#clearSerialMonitorOutputButton').blur();
}

function addAlert(message, category) {
  $( "<div></div>" )
    .addClass("alert alert-dismissable alert-" + category)
    .append("<button type='button' class='close' data-dismiss='alert' aria-hidden='true'>&times;</button>" + message)
    .appendTo("#alertArea");
}

function setHoloseatEnableButton(enabled) {
  if (enabled) {
    $('#holoseatEnableButton').attr("aria-pressed", true);
    $('#holoseatEnableButton').addClass('active');
  }
  else {
    $('#holoseatEnableButton').attr("aria-pressed", false);
    $('#holoseatEnableButton').removeClass('active');
  }
}
