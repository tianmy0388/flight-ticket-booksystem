# flights/forms.py
from django import forms
from django.utils import timezone

from .models import Flight, FlightSeat, CabinClass


class FlightSearchForm(forms.Form):
    """
    前台航班查询表单：
    - 出发地城市：可选
    - 目的地城市：必填
    """
    depart_city = forms.CharField(
        label="出发地城市（可选）",
        max_length=50,
        required=False,
    )
    arrive_city = forms.CharField(
        label="目的地城市",
        max_length=50,
        required=True,
    )
    depart_date = forms.DateField(
        label="出发日期",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    sort = forms.ChoiceField(
        label="排序方式",
        required=False,
        choices=(
            ("price", "按价格排序"),
            ("depart_time", "按起飞时间排序"),
        ),
        initial="price",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给城市字段加 bootstrap 样式
        self.fields["depart_city"].widget.attrs.update({"class": "form-control"})
        self.fields["arrive_city"].widget.attrs.update({"class": "form-control"})

    def clean_depart_date(self):
        d = self.cleaned_data["depart_date"]
        if d < timezone.now().date():
            raise forms.ValidationError("出发日期不能早于今天")
        return d


class FlightAdminForm(forms.ModelForm):
    """
    管理员在后台管理航班时使用的表单：
    - 通过选择出发/到达机场，城市信息由 Airport.city 决定
    - 三个自定义字段：各舱位的“剩余座位数”（available_seats）
    """

    # 显式定义时间字段，保证编辑时能回显到 datetime-local 控件
    depart_time = forms.DateTimeField(
        label="Depart time",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    arrive_time = forms.DateTimeField(
        label="Arrive time",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "form-control"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    # 各舱位“剩余座位数”
    economy_seats = forms.IntegerField(
        label="经济舱剩余座位数",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    business_seats = forms.IntegerField(
        label="公务舱剩余座位数",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    first_seats = forms.IntegerField(
        label="头等舱剩余座位数",
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Flight
        fields = [
            "flight_no",
            "airline",
            "plane_type",
            "depart_airport",
            "arrive_airport",
            "depart_time",
            "arrive_time",
            "base_price",
            "status",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 给除时间以外的字段统一加上 bootstrap 样式
        for name, field in self.fields.items():
            if name in ("depart_time", "arrive_time"):
                continue
            field.widget.attrs.setdefault("class", "form-control")

        # 如果是编辑已有航班，尝试读取各舱位“剩余座位数”作为初始值
        if self.instance and self.instance.pk:
            seats = FlightSeat.objects.filter(flight=self.instance)
            by_cabin = {s.cabin_class: s for s in seats}

            econ = by_cabin.get(CabinClass.ECONOMY)
            if econ:
                self.fields["economy_seats"].initial = econ.available_seats

            biz = by_cabin.get(CabinClass.BUSINESS)
            if biz:
                self.fields["business_seats"].initial = biz.available_seats

            fst = by_cabin.get(CabinClass.FIRST)
            if fst:
                self.fields["first_seats"].initial = fst.available_seats

    def clean(self):
        cleaned = super().clean()
        econ = cleaned.get("economy_seats") or 0
        biz = cleaned.get("business_seats") or 0
        fst = cleaned.get("first_seats") or 0

        # 仅在“新建航班”时要求至少有一个舱位座位数 > 0；
        # 编辑航班时允许全部 0（表示不再售票）
        if not self.instance or not self.instance.pk:
            if econ + biz + fst <= 0:
                raise forms.ValidationError("至少为一个舱位设置大于 0 的座位数。")

        return cleaned
