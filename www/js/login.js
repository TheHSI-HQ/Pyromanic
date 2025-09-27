(function () {
  const backgrounds = [
    {
      width: 854,
      url: "<<base>>/res/img/background-480p.img",
    },
    {
      width: 1280,
      url: "<<base>>/res/img/background-720p.img",
    },
    {
      width: 1920,
      url: "<<base>>/res/img/background-1080p.img",
    },
    {
      width: 3840,
      url: "<<base>>/res/img/background-4k.img",
    },
    {
      width: 7680,
      url: "<<base>>/res/img/background-8k.img",
    },
  ];

  function loadProgressiveBackground() {
    const screenWidth = window.innerWidth;
    const stages = backgrounds.filter((b) => b.width <= screenWidth);
    (function loadNext(i) {
      if (i >= stages.length) {
        if (backgrounds[i - 1].width <= 1920)
          document.body.style.backgroundImage = `url('<<base>>/res/img/background-1080pHD.img')`;
        return;
      }
      const img = new Image();
      img.src = stages[i].url;
      img.onload = () => {
        document.body.style.backgroundImage = `url('${stages[i].url}')`;
        loadNext(i + 1);
      };
    })(0);
  }
  window.addEventListener("load", loadProgressiveBackground);
  document.addEventListener("DOMContentLoaded", () => {
    if (window.location.protocol != "https:") {
      document.getElementById("http-warning").classList.remove("hidden");
      document.getElementById("container").remove();
      return;
    }
    document.getElementById("show-button").addEventListener("mousedown", () => {
      document.getElementById("show-button").querySelector("img").src =
        "res/img/icon-eye_on.img";
      document.getElementById("pyro-password").type = "text";
    });
    document.getElementById("show-button").addEventListener("mouseup", () => {
      document.getElementById("show-button").querySelector("img").src =
        "res/img/icon-eye_off.img";
      document.getElementById("pyro-password").type = "password";
    });
    document.querySelector(".emblem-logo").addEventListener("click", () => {
      let a = document.createElement("a");
      a.href = "https://www.thehsi.cloud/";
      a.target = "_blank";
      a.rel = "noopener";
      a.click();
    });
    document.getElementById("submit").addEventListener("click", (e) => {
      e.preventDefault(true);
      let username = document.getElementById("pyro-username");
      let password = document.getElementById("pyro-password");
      if (username.value == "") {
        username.focus();
        return;
      }
      if (password.value == "") {
        password.focus();
        return;
      }
      let form = document.createElement("form");
      let username_field = document.createElement("input");
      let password_field = document.createElement("input");
      username_field.value = username.value;
      username_field.name = "username";
      username_field.type = "hidden";
      password_field.value = password.value;
      password_field.name = "password";
      password_field.type = "hidden";
      form.appendChild(username_field);
      form.appendChild(password_field);
      form.action = "<<base>>/letmein" + location.search;
      form.method = "POST";
      document.body.appendChild(form);
      console.log(form);
      form.submit();
      form.remove();
    });
    document
      .getElementById("pyro-username")
      .addEventListener("keypress", (e) => {
        if (e.key.toLowerCase() == "enter") {
          let username = document.getElementById("pyro-username");
          let password = document.getElementById("pyro-password");
          if (password.value == "") {
            password.focus();
            e.preventDefault(true);
            return;
          }
          if (username.value == "") {
            username.focus();
            e.preventDefault(true);
            return;
          }
          document.getElementById("submit").click();
        }
      });
    document
      .getElementById("pyro-password")
      .addEventListener("keypress", (e) => {
        if (e.key.toLowerCase() == "enter") {
          let username = document.getElementById("pyro-username");
          let password = document.getElementById("pyro-password");
          if (username.value == "") {
            username.focus();
            e.preventDefault(true);
            return;
          }
          if (password.value == "") {
            password.focus();
            e.preventDefault(true);
            return;
          }
          document.getElementById("submit").click();
        }
      });
  });
})();
