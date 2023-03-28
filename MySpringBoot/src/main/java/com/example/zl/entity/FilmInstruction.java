package com.example.zl.entity;

public class FilmInstruction {

    private int id;
    private String jobname;
    private String inplanJob;
    private String stepname;
    private String processname;
    private String face;
    private char checkNo;
    private String checkProjectName;
    private String standardValue;
    private String upperlimit;
    private String lowerlimit;
    private String notes;
    private String imageNameOrigin;
    private String imageName;
    private String oprUser;
    private String oprUserInplan;
    private String oprIp;
    private String fromJob;
    private String isLock;
    private String oprTime;
    private String index1;
    private String toplayer;
    private String botlayer;
    private String artWorktracesidth;
    private String imp;
    private String coordinate;
    private String life_lw;
    private String messureType;
    private String direction;

    public FilmInstruction() {
    }

    public FilmInstruction(String inplanJob, String face, char checkNo, String checkProjectName, String standardValue, String notes, String imageName, String oprUser, String oprUserInplan, String oprIp, String oprTime, String coordinate, String messureType) {
        this.inplanJob = inplanJob;
        this.face = face;
        this.checkNo = checkNo;
        this.checkProjectName = checkProjectName;
        this.standardValue = standardValue;
        this.notes = notes;
        this.imageName = imageName;
        this.oprUser = oprUser;
        this.oprUserInplan = oprUserInplan;
        this.oprIp = oprIp;
        this.oprTime = oprTime;
        this.coordinate = coordinate;
        this.messureType = messureType;
    }

    public FilmInstruction(int id, String jobname, String inplanJob, String stepname, String processname, String face, char checkNo, String checkProjectName, String standardValue, String upperlimit, String lowerlimit, String notes, String imageNameOrigin, String imageName, String oprUser, String oprUserInplan, String oprIp, String fromJob, String isLock, String oprTime, String index1, String toplayer, String botlayer, String artWorktracesidth, String imp, String coordinate, String life_lw, String messureType, String direction) {
        this.id = id;
        this.jobname = jobname;
        this.inplanJob = inplanJob;
        this.stepname = stepname;
        this.processname = processname;
        this.face = face;
        this.checkNo = checkNo;
        this.checkProjectName = checkProjectName;
        this.standardValue = standardValue;
        this.upperlimit = upperlimit;
        this.lowerlimit = lowerlimit;
        this.notes = notes;
        this.imageNameOrigin = imageNameOrigin;
        this.imageName = imageName;
        this.oprUser = oprUser;
        this.oprUserInplan = oprUserInplan;
        this.oprIp = oprIp;
        this.fromJob = fromJob;
        this.isLock = isLock;
        this.oprTime = oprTime;
        this.index1 = index1;
        this.toplayer = toplayer;
        this.botlayer = botlayer;
        this.artWorktracesidth = artWorktracesidth;
        this.imp = imp;
        this.coordinate = coordinate;
        this.life_lw = life_lw;
        this.messureType = messureType;
        this.direction = direction;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }

    public String getJobname() {
        return jobname;
    }

    public void setJobname(String jobname) {
        this.jobname = jobname;
    }

    public String getInplanJob() {
        return inplanJob;
    }

    public void setInplanJob(String inplanJob) {
        this.inplanJob = inplanJob;
    }

    public String getStepname() {
        return stepname;
    }

    public void setStepname(String stepname) {
        this.stepname = stepname;
    }

    public String getProcessname() {
        return processname;
    }

    public void setProcessname(String processname) {
        this.processname = processname;
    }

    public String getFace() {
        return face;
    }

    public void setFace(String face) {
        this.face = face;
    }

    public char getCheckNo() {
        return checkNo;
    }

    public void setCheckNo(char checkNo) {
        this.checkNo = checkNo;
    }

    public String getCheckProjectName() {
        return checkProjectName;
    }

    public void setCheckProjectName(String checkProjectName) {
        this.checkProjectName = checkProjectName;
    }

    public String getStandardValue() {
        return standardValue;
    }

    public void setStandradValue(String standardValue) {
        this.standardValue = standardValue;
    }

    public String getUpperlimit() {
        return upperlimit;
    }

    public void setUpperlimit(String upperlimit) {
        this.upperlimit = upperlimit;
    }

    public String getLowerlimit() {
        return lowerlimit;
    }

    public void setLowerlimit(String lowerlimit) {
        this.lowerlimit = lowerlimit;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public String getImageNameOrigin() {
        return imageNameOrigin;
    }

    public void setImageNameOrigin(String imageNameOrigin) {
        this.imageNameOrigin = imageNameOrigin;
    }

    public String getImageName() {
        return imageName;
    }

    public void setImageName(String imageName) {
        this.imageName = imageName;
    }

    public String getOprUser() {
        return oprUser;
    }

    public void setOprUser(String oprUser) {
        this.oprUser = oprUser;
    }

    public String getOprUserInplan() {
        return oprUserInplan;
    }

    public void setOprUserInplan(String oprUserInplan) {
        this.oprUserInplan = oprUserInplan;
    }

    public String getOprIp() {
        return oprIp;
    }

    public void setOprIp(String oprIp) {
        this.oprIp = oprIp;
    }

    public String getFromJob() {
        return fromJob;
    }

    public void setFromJob(String fromJob) {
        this.fromJob = fromJob;
    }

    public String getIsLock() {
        return isLock;
    }

    public void setIsLock(String isLock) {
        this.isLock = isLock;
    }

    public String getOprTime() {
        return oprTime;
    }

    public void setOprTime(String oprTime) {
        this.oprTime = oprTime;
    }

    public String getIndex1() {
        return index1;
    }

    public void setIndex1(String index1) {
        this.index1 = index1;
    }

    public String getToplayer() {
        return toplayer;
    }

    public void setToplayer(String toplayer) {
        this.toplayer = toplayer;
    }

    public String getBotlayer() {
        return botlayer;
    }

    public void setBotlayer(String botlayer) {
        this.botlayer = botlayer;
    }

    public String getArtWorktracesidth() {
        return artWorktracesidth;
    }

    public void setArtWorktracesidth(String artWorktracesidth) {
        this.artWorktracesidth = artWorktracesidth;
    }

    public String getImp() {
        return imp;
    }

    public void setImp(String imp) {
        this.imp = imp;
    }

    public String getCoordinate() {
        return coordinate;
    }

    public void setCoordinate(String coordinate) {
        this.coordinate = coordinate;
    }

    public String getLife_lw() {
        return life_lw;
    }

    public void setLife_lw(String life_lw) {
        this.life_lw = life_lw;
    }

    public String getMessureType() {
        return messureType;
    }

    public void setMessureType(String messureType) {
        this.messureType = messureType;
    }

    public String getDirection() {
        return direction;
    }

    public void setDirection(String direction) {
        this.direction = direction;
    }

    @Override
    public String toString() {
        return "FilmInstruction{" +
                "id=" + id +
                ", jobname='" + jobname + '\'' +
                ", inplanJob='" + inplanJob + '\'' +
                ", stepname='" + stepname + '\'' +
                ", processname='" + processname + '\'' +
                ", face='" + face + '\'' +
                ", checkNo=" + checkNo +
                ", checkProjectName='" + checkProjectName + '\'' +
                ", standardValue='" + standardValue + '\'' +
                ", upperlimit='" + upperlimit + '\'' +
                ", lowerlimit='" + lowerlimit + '\'' +
                ", notes='" + notes + '\'' +
                ", imageNameOrigin='" + imageNameOrigin + '\'' +
                ", imageName='" + imageName + '\'' +
                ", oprUser='" + oprUser + '\'' +
                ", oprUserInplan='" + oprUserInplan + '\'' +
                ", oprIp='" + oprIp + '\'' +
                ", fromJob='" + fromJob + '\'' +
                ", isLock='" + isLock + '\'' +
                ", oprTime='" + oprTime + '\'' +
                ", index1='" + index1 + '\'' +
                ", toplayer='" + toplayer + '\'' +
                ", botlayer='" + botlayer + '\'' +
                ", artWorktracesidth='" + artWorktracesidth + '\'' +
                ", imp='" + imp + '\'' +
                ", coordinate='" + coordinate + '\'' +
                ", life_lw='" + life_lw + '\'' +
                ", messureType='" + messureType + '\'' +
                ", direction='" + direction + '\'' +
                '}';
    }
}
