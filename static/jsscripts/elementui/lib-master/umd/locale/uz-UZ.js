(function (global, factory) {
  if (typeof define === "function" && define.amd) {
    define('element/locale/uz-UZ', ['module', 'exports'], factory);
  } else if (typeof exports !== "undefined") {
    factory(module, exports);
  } else {
    var mod = {
      exports: {}
    };
    factory(mod, mod.exports);
    global.ELEMENT.lang = global.ELEMENT.lang || {}; 
    global.ELEMENT.lang.uzUZ = mod.exports;
  }
})(this, function (module, exports) {
  'use strict';

  exports.__esModule = true;
  exports.default = {
    el: {
      colorpicker: {
        confirm: 'Qabul qilish',
        clear: 'Tozalash'
      },
      datepicker: {
        now: 'Hozir',
        today: 'Bugun',
        cancel: 'Bekor qilish',
        clear: 'Tozalash',
        confirm: 'Qabul qilish',
        selectDate: 'Kunni tanlash',
        selectTime: 'Soatni tanlash',
        startDate: 'Boshlanish sanasi',
        startTime: 'Boshlanish vaqti',
        endDate: 'Tugash sanasi',
        endTime: 'Tugash vaqti',
        prevYear: 'Oʻtgan yil',
        nextYear: 'Kelgusi yil',
        prevMonth: 'Oʻtgan oy',
        nextMonth: 'Kelgusi oy',
        year: 'Yil',
        month1: 'Yanvar',
        month2: 'Fevral',
        month3: 'Mart',
        month4: 'Aprel',
        month5: 'May',
        month6: 'Iyun',
        month7: 'Iyul',
        month8: 'Avgust',
        month9: 'Sentabr',
        month10: 'Oktabr',
        month11: 'Noyabr',
        month12: 'Dekabr',
        week: 'Hafta',
        weeks: {
          sun: 'Yak',
          mon: 'Dush',
          tue: 'Sesh',
          wed: 'Chor',
          thu: 'Pay',
          fri: 'Jum',
          sat: 'Shan'
        },
        months: {
          jan: 'Yan',
          feb: 'Fev',
          mar: 'Mar',
          apr: 'Apr',
          may: 'May',
          jun: 'Iyun',
          jul: 'Iyul',
          aug: 'Avg',
          sep: 'Sen',
          oct: 'Okt',
          nov: 'Noy',
          dec: 'Dek'
        }
      },
      select: {
        loading: 'Yuklanmoqda',
        noMatch: 'Mos ma'lumot yoʻq',
        noData: 'Ma'lumot yoʻq',
        placeholder: 'Tanladizngiz'
      },
      cascader: {
        noMatch: 'Mos ma'lumot topilmadi',
        loading: 'Yuklanmoqda',
        placeholder: 'Tanlash',
        noData: 'Ma'lumot yoʻq'
      },
      pagination: {
        goto: 'Oʻtish',
        pagesize: '/sahifa',
        total: 'Barchasi {total} ta',
        pageClassifier: ''
      },
      messagebox: {
        title: 'Xabar',
        confirm: 'Qabul qilish',
        cancel: 'Bekor qilish',
        error: 'Xatolik'
      },
      upload: {
        deleteTip: 'Oʻchirish tugmasini bosib oʻchiring',
        delete: 'Oʻchirish',
        preview: 'Oldin koʻrish',
        continue: 'Davom qilish'
      },
      table: {
        emptyText: 'Boʻsh',
        confirmFilter: 'Qabul qilish',
        resetFilter: 'Oldingi holatga qaytarish',
        clearFilter: 'Jami',
        sumText: 'Summasi'
      },
      tree: {
        emptyText: 'Ma'lumot yoʻq'
      },
      transfer: {
        noMatch: 'Mos ma'lumot topilmadi',
        noData: 'Ma'lumot yoʻq',
        titles: ['1-jadval', '2-jadval'],
        filterPlaceholder: 'Kalit soʻzni kiriting',
        noCheckedFormat: '{total} ta element',
        hasCheckedFormat: '{checked}/{total} ta belgilandi'
      },
      image: {
        error: 'Xatolik'
      },
      pageHeader: {
        title: 'Orqaga'
      },
      popconfirm: {
        confirmButtonText: 'Yes', // to be translated
        cancelButtonText: 'No' // to be translated
      },
      empty: {
        description: 'Boʻsh'
      }
    }
  };
  module.exports = exports['default'];
});